# Izipay Payment Module — Blueprint para Salesianos FEST

> **Project:** Salesianos (Centro de Esparcimiento — Salesianos FEST)  
> **Date:** 2026-09-21  
> **Type:** Architecture Exploration (referenced app: `centro-de-esparcimiento` / `ninja`)  
> **Status:** La app de referencia ya tiene el módulo funcionando. Salesianos FEST aún NO.

---

## 1. Resumen ejecutivo

El módulo de pagos de la app de referencia (`centro-de-esparcimiento`) ya está implementado y sirve como **blueprint** para implementar el mismo flujo en Salesianos FEST. Ambos proyectos comparten:

- Stack backend: Django + Ninja + PostgreSQL
- Stack frontend: Next.js + TypeScript + TanStack Query
- Pasarela de pagos: **Izipay Web Core 2.0** (Pop-up)
- Multi-tenancy: cada usuario/responsable paga su propia inscripción

La app de referencia demuestra que el patrón funciona en producción con un dominio equivalente (ingresos y visitas vs. inscripciones deportivas).

**Diferencia clave**: la app de referencia gestiona `OrdenDeCobro → Pagos` para entradas y reservas. Salesianos FEST necesita el mismo patrón pero atado a `Inscripción → Pagos`.

---

## 2. Arquitectura (de la app de referencia)

```
Usuario                  Frontend                       Backend (Ninja)                 Izipay
   │                        │                                │                            │
   │ Click "Pagar"─────────>│                                │                            │
   │                        │ GET /api/finanzas/pagos/       │                            │
   │                        │      izipay/preparar/{orden_id}│                            │
   │                        ├───────────────────────────────>│                            │
   │                        │                                │ POST /security/v1/Token/Generate
   │                        │                                ├───────────────────────────>│
   │                        │                                │<─ { token, transactionId, │
   │                        │                                │    order, billing,        │
   │                        │                                │    shipping }             │
   │                        │<── { success, token, ... } ───│                            │
   │                        │                                                    │
   │                        │ window.Izipay SDK (cargado por SDK URL)             │
   │                        │───────────────────────────────────────────────────────>│
   │                        │   ↓ pop-up Izipay                                  │
   │ Ingresa datos tarjeta   │                                                    │
   │ Confirma pago          │                                                    │
   │                        │ callbackResponsePayment({ code: '00', ... })         │
   │                        │                                                    │
   │                        │ POST /api/finanzas/pagos/izipay/confirmar            │
   │                        │  { orden_id, kr_answer }                           │
   │                        ├───────────────────────────────>│                            │
   │                        │                                │ IzipayService.verificar_y_registrar
   │                        │                                │ PagoService.registrar_pago (TARJETA)
   │                        │                                │ PagoService.actualizar_saldo_orden
   │                        │<── { success: true } ──────────│                            │
   │<── toast success ──────│                                │                            │
```

---

## 3. Backend — Modelo completo (de la app de referencia)

### 3.1 Modelo `OrdenDeCobro` (UUIDModel + TimestampedModel)

```python
# domains/finanzas/models/orden_cobro.py
class OrdenDeCobro(UUIDModel, TimestampedModel):
    estado = CharField(choices=EstadoOrden, default=PENDIENTE, max_length=20)
    fecha_limite_pago = DateTimeField(null=True, blank=True)
    fecha_limite_cancelacion = DateTimeField(null=True, blank=True)
    cliente = ForeignKey(Usuario, on_delete=PROTECT, related_name='ordenes_cobro')
    concepto_principal = CharField(max_length=200)
    monto_total = DecimalField(max_digits=10, decimal_places=2, default=0)
    saldo_pendiente = DecimalField(max_digits=10, decimal_places=2, default=0)
    esta_pagada = BooleanField(default=False)

    history = HistoricalRecords()  # django-simple-history
```

### 3.2 Modelo `Pago` (UUIDModel + TimestampedModel + HistoricalRecords)

```python
# domains/finanzas/models/pago.py
class TipoMovimientoDinero(TextChoices):
    INGRESO = "INGRESO", "Ingreso (Cobro a cliente)"
    EGRESO = "EGRESO", "Egreso (Devolución/Reembolso al cliente)"

class MetodoPago(TextChoices):
    EFECTIVO = "EFECTIVO", "Efectivo"
    YAPE_PLIN = "YAPE_PLIN", "Yape / Plin"
    TARJETA = "TARJETA", "Tarjeta (Visa/Mastercard)"
    TRANSFERENCIA = "TRANSFERENCIA", "Transferencia Bancaria"
    OTRO = "OTRO", "Otro / Cortesía"

class Pago(UUIDModel, TimestampedModel):
    orden = ForeignKey(OrdenDeCobro, on_delete=PROTECT, related_name="pagos")
    cajero = ForeignKey(Usuario, on_delete=PROTECT)  # Quién registró
    tipo = CharField(choices=TipoMovimientoDinero, default=INGRESO, max_length=20)
    monto = DecimalField(max_digits=10, decimal_places=2)
    metodo = CharField(choices=MetodoPago, max_length=20)
    referencia = CharField(max_length=100, blank=True)
    tipo_comprobante = CharField(max_length=50, blank=True)  # BOLETA/FACTURA/RECIBO_INTERNO
    serie_correlativo = CharField(max_length=50, blank=True)
    metadatos = JSONField(default=dict, blank=True)  # Izipay full response
    history = HistoricalRecords()
```

### 3.3 Estados de Orden

```python
# domains/finanzas/constants.py
class EstadoOrden(TextChoices):
    PENDIENTE = "PENDIENTE", "Pendiente (Esperando pago)"
    PAGADA = "PAGADA", "Pagada (Completadas)"
    VENCIDA = "VENCIDA", "Vencida (Plazo expirado)"
    ANULADA = "ANULADA", "Anulada (Cancelado administrativamente)"
    REEMBOLSADA = "REEMBOLSADA", "Reembolsada"
```

---

## 4. Backend — Servicios (de la app de referencia)

### 4.1 `PagoService` — matemática contable

```python
# domains/finanzas/services/pago_service.py
class PagoService:

    @staticmethod
    def actualizar_saldo_orden(orden: OrdenDeCobro) -> None:
        """Recalcula saldo_pendiente sumando pagos INGRESO - EGRESO."""
        ingresos = orden.pagos.filter(tipo=INGRESO).aggregate(total=Sum("monto"))["total"] or Decimal("0.00")
        egresos = orden.pagos.filter(tipo=EGRESO).aggregate(total=Sum("monto"))["total"] or Decimal("0.00")
        dinero_neto = ingresos - egresos
        orden.saldo_pendiente = (orden.monto_total - dinero_neto).quantize(Decimal("0.00"))
        orden.esta_pagada = orden.saldo_pendiente <= Decimal("0.00")
        if orden.esta_pagada and orden.estado not in [ANULADA, REEMBOLSADA]:
            orden.estado = PAGADA
        orden.save()

    @staticmethod
    def registrar_pago(orden_id, cajero_id, metodo, monto=None, tipo=INGRESO,
                      referencia="", metadatos=None) -> Pago:
        """Registra entrada o salida de dinero."""
        orden = OrdenDeCobro.objects.get(id=orden_id)
        if orden.estado_real == VENCIDA:
            raise HttpError(400, "Esta orden ha expirado...")
        if monto is None: monto = orden.saldo_pendiente
        if monto <= 0: raise HttpError(400, "Monto debe ser mayor a 0")
        pago = Pago.objects.create(
            orden_id=orden_id, cajero_id=cajero_id, monto=monto,
            metodo=metodo, tipo=tipo, referencia=referencia,
            metadatos=metadatos or {},
        )
        PagoService.actualizar_saldo_orden(orden)
        return pago
```

### 4.2 `IzipayService` — integración con Izipay Web Core 2.0

```python
# domains/finanzas/services/izipay_service.py
class IzipayService:
    
    ENDPOINT_TOKEN = "https://sandbox-api-pw.izipay.pe/security/v1/Token/Generate"

    @staticmethod
    def _sanitizar_texto(texto: str) -> str:
        """Quita acentos y mantiene solo A-Z y espacios."""
        # ... (ver implementación real)

    @staticmethod
    def generar_token_sesion(orden_id: str) -> dict:
        """
        POST /security/v1/Token/Generate
        Retorna: { success, token, transactionId, orderNumber, amount,
                  merchantCode, order, billing, shipping }
        """
        orden = OrdenDeCobro.objects.get(id=orden_id)
        PagoService.actualizar_saldo_orden(orden)  # Sync before
        if orden.esta_pagada:
            return {"success": False, "error": "Ya pagada"}
        if orden.saldo_pendiente <= 0:
            orden.esta_pagada = True
            orden.estado = PAGADA
            orden.save()
            return {"success": False, "error": "Saldo 0"}

        transaction_id = str(int(time.time() * 1000)).rjust(14, "0")[:14]
        order_number = str(int(time.time() * 1000))[:10]
        hp_timestamp = str(int(time.time() * 1000000))
        shop_id = settings.IZIPAY_SHOP_ID
        api_key = settings.IZIPAY_KEY

        payload = {
            "requestSource": "ECOMMERCE",
            "merchantCode": shop_id,
            "orderNumber": order_number,
            "publicKey": api_key,
            "amount": f"{orden.saldo_pendiente:.2f}",
            "currency": "PEN",
            "clientData": {
                "email": cliente.email or "cliente@club.org.pe",
                "fullName": sanitized_name(persona),
                "phoneNumber": persona.celular or "999999999",
                "documentNumber": persona.dni or "00000000",
                "documentType": "DNI",
            },
        }
        headers = {"Authorization": f"Bearer {api_key}", ...}

        with httpx.Client() as client:
            res = client.post(ENDPOINT_TOKEN, json=payload, headers=headers)
            token = res.json().get("token")
            if token:
                return {
                    "success": True,
                    "token": token,
                    "merchantCode": shop_id,
                    "transactionId": transaction_id,
                    "orderNumber": order_number,
                    "amount": f"{orden.saldo_pendiente:.2f}",
                    "order": {"orderNumber": ..., "currency": "PEN",
                              "amount": ..., "processType": "AT",
                              "merchantBuyerId": persona.dni or "00000000",
                              "dateTimeTransaction": hp_timestamp},
                    "billing": {first_name, last_name, email, phone, street,
                                city, state, country, postalCode, documentType, document},
                    "shipping": {...idéntico a billing...},
                }
        return {"success": False, "error": "..."}

    @staticmethod
    def verificar_y_registrar(kr_answer: dict, orden_id: str, cajero_id: str) -> dict:
        """
        Verifica y registra el pago Izipay.
        Idempotente: si transactionId ya existe, retorna success sin duplicar.
        """
        if kr_answer.get("code") == "00":
            # 1. Idempotencia: check por referencia (transactionId)
            if Pago.objects.filter(referencia=transaction_id).exists():
                PagoService.actualizar_saldo_orden(orden)
                return {"success": True, "mensaje": "Ya registrado"}
            # 2. Registrar pago TARJETA
            if orden.saldo_pendiente > 0:
                PagoService.registrar_pago(
                    orden_id=orden_id, cajero_id=cajero_id,
                    metodo="TARJETA", monto=monto_pagado,
                    referencia=transaction_id, metadatos=kr_answer,
                )
            PagoService.actualizar_saldo_orden(orden)
            return {"success": True, "mensaje": "Pago procesado"}
        return {"success": False, "error": response_message}
```

---

## 5. Backend — Schemas API (Ninja)

```python
# domains/finanzas/schemas/pago.py
class PagoManualIn(Schema):
    """Payload para registrar un pago manual (Efectivo/Transferencia)."""
    orden_id: str
    monto: Optional[Decimal] = None
    metodo: str
    referencia: Optional[str] = ""

class PagoOut(ModelSchema):
    cajero_nombre: str = ""
    cuenta_origen: str = ""

    class Meta:
        model = Pago
        fields = ["id", "monto", "metodo", "tipo", "referencia",
                  "created_at", "metadatos"]

class IzipayTokenOut(Schema):
    success: bool
    token: Optional[str] = None
    transactionId: Optional[str] = None
    orderNumber: Optional[str] = None
    amount: Optional[str] = None
    merchantCode: Optional[str] = None
    order: Optional[Dict[str, Any]] = None
    billing: Optional[Dict[str, Any]] = None
    shipping: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class IzipayConfirmIn(Schema):
    orden_id: str
    kr_answer: Dict[str, Any]
```

---

## 6. Backend — Controller (Ninja)

```python
# domains/finanzas/api/pagos.py
@api_controller("/finanzas/pagos", tags=["Finanzas (Pagos)"], auth=JWTAuth())
class PagosController(ControllerBase):

    @route.post(
        "/confirmar-manual",
        response=PagoOut,
        permissions=[CheckPermission(PermisosPagos.GESTIONAR_PAGOS)],
    )
    def confirmar_pago_manual(self, payload: PagoManualIn):
        """Confirma un pago manual (Efectivo/Transferencia/Yape)."""
        cajero = self.context.request.auth
        with transaction.atomic():
            pago = PagoService.registrar_pago(
                orden_id=payload.orden_id,
                cajero_id=str(cajero.id),
                monto=payload.monto,
                metodo=payload.metodo,
                referencia=payload.referencia,
            )
        return pago

    @route.get("/izipay/preparar/{orden_id}", response=IzipayTokenOut)
    def preparar_pago_izipay(self, orden_id: str):
        """Genera token de sesión para Izipay."""
        return IzipayService.generar_token_sesion(orden_id)

    @route.post("/izipay/confirmar", response=dict)
    def confirmar_pago_izipay(self, payload: IzipayConfirmIn):
        """Verifica y registra el resultado del pago Izipay."""
        cajero = self.context.request.auth
        return IzipayService.verificar_y_registrar(
            kr_answer=payload.kr_answer,
            orden_id=payload.orden_id,
            cajero_id=str(cajero.id),
        )
```

**Endpoints resultantes** (3 totales):
- `GET /api/finanzas/pagos/izipay/preparar/{orden_id}`
- `POST /api/finanzas/pagos/izipay/confirmar`
- `POST /api/finanzas/pagos/confirmar-manual`

---

## 7. Frontend — Modal Izipay (de la app de referencia)

### 7.1 `IzipayModal.tsx` (componente cliente)

```tsx
"use client";

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import api from "@/lib/api/config";

declare global {
  interface Window {
    Izipay?: any;
  }
}

const IZIPAY_RSA_KEY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8..."; // Public RSA key

const getCurrentTransactionTime = () => (Date.now() * 1000).toString();

const normalizeAmount = (value: unknown): string => {
  const n = Number(value);
  return Number.isFinite(n) && n > 0 ? n.toFixed(2) : "1.00";
};

const sanitizeNamePart = (value: unknown, fallback: string): string => {
  // Quita acentos, números, caracteres especiales. 
  // Rechaza títulos/placeholders ("Ing", "Dr", "Test", "Usuario").
  const cleaned = String(value ?? "").normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z\s]/g, " ")
    .replace(/\s+/g, " ").trim();
  const forbidden = ["ing", "dr", "dra", "sr", "sra", "test", "usuario"];
  if (!cleaned || forbidden.includes(cleaned.toLowerCase())) return fallback;
  return cleaned;
};

const sanitizePhone = (v: unknown): string => {
  const digits = String(v ?? "").replace(/\D/g, "");
  return digits.length >= 7 ? digits.slice(0, 15) : "999999999";
};

const sanitizeDocument = (v: unknown): string => {
  const digits = String(v ?? "").replace(/\D/g, "");
  return digits.length >= 8 ? digits.slice(0, 12) : "12345678";
};

const sanitizeEmail = (v: unknown): string => {
  const e = String(v ?? "").trim();
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e) ? e : "pagos@ciplima.pe";
};

const buildAddressData = (raw: any) => ({
  ...raw,
  firstName: sanitizeNamePart(raw?.firstName, "Juan"),
  lastName: sanitizeNamePart(raw?.lastName, "Perez"),
  email: sanitizeEmail(raw?.email),
  phoneNumber: sanitizePhone(raw?.phoneNumber),
  street: "1295 Charleston Road",
  city: "Lima",
  state: "Lima",
  country: "PE",
  postalCode: "00001",
  documentType: sanitizeText(raw?.documentType) || "DNI",
  document: sanitizeDocument(raw?.document),
});

export function IzipayModal({ isOpen, onClose, ordenId, onSuccess }: IzipayModalProps) {
  const [loading, setLoading] = useState(false);

  const handleLaunchIzipay = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get(`/api/finanzas/pagos/izipay/preparar/${ordenId}`);
      const data = response.data;

      if (!data.success || !data.token) {
        toast.error(data.error || "No se pudo generar el token.");
        onClose();
        return;
      }

      // Esperar al SDK global Izipay (polling 30×100ms)
      let retries = 0;
      while (!window.Izipay && retries < 30) {
        await new Promise(r => setTimeout(r, 100));
        retries++;
      }
      if (!window.Izipay) {
        toast.error("El SDK de Izipay no se ha cargado correctamente.");
        onClose();
        return;
      }

      // Construir config final respetando payload del backend
      const baseConfig = data.config && typeof data.config === "object"
        ? data.config : data;
      const orderFromBackend = baseConfig.order || {};
      const billingFromBackend = baseConfig.billing || data.billing || {};
      const shippingFromBackend = baseConfig.shipping || data.shipping || billingFromBackend;

      const finalConfig = {
        action: baseConfig.action || "pay",
        merchantCode: String(baseConfig.merchantCode ?? data.merchantCode ?? ""),
        transactionId: String(baseConfig.transactionId ?? data.transactionId ?? ""),
        order: {
          ...orderFromBackend,
          orderNumber: String(orderFromBackend.orderNumber ?? data.orderNumber ?? ""),
          currency: orderFromBackend.currency || "PEN",
          amount: normalizeAmount(orderFromBackend.amount ?? data.amount),
          processType: orderFromBackend.processType || "AT",
          payMethod: "CARD,QR,YAPE_CODE,PAGO_PUSH",
          merchantBuyerId: orderFromBackend.merchantBuyerId || billingFromBackend.document || "00000000",
          dateTimeTransaction: getCurrentTransactionTime(),
        },
        billing: buildAddressData(billingFromBackend),
        shipping: buildAddressData(shippingFromBackend),
        render: {
          ...(baseConfig.render || {}),
          typeForm: "pop-up",
          container: "#izipay-checkout",
          showButtonProcessForm: baseConfig.render?.showButtonProcessForm ?? true,
        },
        language: baseConfig.language,
        urlRedirect: baseConfig.urlRedirect,
        appearance: baseConfig.appearance,
        originEntry: baseConfig.originEntry,
        customFields: Array.isArray(baseConfig.customFields) ? baseConfig.customFields : [],
      };

      const checkout = new window.Izipay({ config: finalConfig });

      const callbackResponsePayment = async (izipayResponse: any) => {
        const methodUsed = izipayResponse.paymentMethod || izipayResponse.brand || "Izipay";
        if (izipayResponse.code === "00") {
          const confirmRes = await api.post("/api/finanzas/pagos/izipay/confirmar", {
            orden_id: ordenId,
            kr_answer: izipayResponse,
          });
          if (confirmRes.data.success) {
            toast.success(`Pago con ${methodUsed} realizado con éxito.`);
            onSuccess();
            onClose();
          } else {
            toast.error(confirmRes.data.error || "Error al confirmar el pago.");
          }
        } else {
          toast.error(izipayResponse.message || "Pago rechazado por Izipay.");
        }
      };

      checkout.on("payment.response", callbackResponsePayment);
      checkout.renderCheckout();
    } catch (e) {
      console.error(e);
      toast.error("Error al iniciar el pago con Izipay.");
    } finally {
      setLoading(false);
    }
  }, [ordenId, onClose, onSuccess]);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Pagar con Izipay</DialogTitle>
        </DialogHeader>
        <div id="izipay-checkout" />
        {loading && <Loader2 className="animate-spin" />}
      </DialogContent>
    </Dialog>
  );
}
```

### 7.2 Hook `usePagoActions` (TanStack Query)

```ts
// hooks/finanzas/usePagoActions.ts
export interface PagoManualPayload {
  orden_id: string;
  monto: number;
  metodo: "EFECTIVO" | "TRANSFERENCIA" | "YAPE" | "PLIN" | "OTRO";
  referencia: string;
}

export function usePagoActions() {
  const queryClient = useQueryClient();

  const registrarPagoManual = useMutation({
    mutationFn: async (payload: PagoManualPayload) => {
      const { data } = await api.post(
        "/api/finanzas/pagos/confirmar-manual",
        payload,
      );
      return data;
    },
    onSuccess: () => {
      toast.success("Pago registrado correctamente");
      queryClient.invalidateQueries({ queryKey: ["visitas"] });
      queryClient.invalidateQueries({ queryKey: ["visita"] });
    },
    onError: (err) => {
      toast.error(getErrorMessage(err));
    },
  });

  return { registrarPagoManual };
}
```

---

## 8. Settings de Izipay (de la app de referencia)

```python
# config/settings/base.py
IZIPAY_SHOP_ID = env("IZIPAY_SHOP_ID", default="")
IZIPAY_KEY = env("IZIPAY_KEY", default="")  # Bearer token
```

**Frontend (`ninja-front/.env.local`):**

```bash
# SDK Izipay — se carga en el layout raíz (no desde .env)
# Ver sección 10 para snippet
```

---

## 9. Palabras clave y constantes del módulo

| Concepto | Valor |
|----------|-------|
| Provider | `izipay` |
| Nombre comercial | izipay |
| Constante settings backend | `IZIPAY_SHOP_ID`, `IZIPAY_KEY` |
| Constante frontend | `window.Izipay` (SDK global) |
| Endpoint backend API Izipay | `https://sandbox-api-pw.izipay.pe/security/v1/Token/Generate` |
| Endpoints app Izipay | `/api/finanzas/pagos/{izipay/preparar/{id}, izipay/confirmar, confirmar-manual}` |
| Container DOM pop-up | `#izipay-checkout` |
| Render mode | `typeForm: "pop-up"` |
| Pay methods soportados | `CARD,QR,YAPE_CODE,PAGO_PUSH` |
| Process type | `AT` (Authorization + capture) |
| Estado éxito Izipay | `code === "00"` |
| Idempotencia | `Pago.objects.filter(referencia=transaction_id).exists()` |
| Tipo comprobante | `BOLETA` / `FACTURA` / `RECIBO_INTERNO` |
| Moneda | `PEN` |

---

## 10. Carga del SDK Izipay en el layout raíz (frontend)

El SDK Izipay se carga globalmente en el layout raíz de la app (`app/layout.tsx`). Ejemplo en la app de referencia:

```tsx
// app/layout.tsx
import Script from "next/script";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <head>
        <Script
          src="https://sandbox-api-pw.izipay.pe/js/v1/checkout.js"
          strategy="beforeInteractive"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
```

Alternativa recomendada para Salesianos FEST con variables de entorno:

```tsx
const IZIPAY_SDK_URL = process.env.NEXT_PUBLIC_IZIPAY_SDK_URL
  || "https://sandbox-api-pw.izipay.pe/js/v1/checkout.js";
const IZIPAY_MODE = process.env.NEXT_PUBLIC_IZIPAY_MODE ?? "test";

const SDK_URL = IZIPAY_MODE === "production"
  ? "https://api.izipay.pe/js/v1/checkout.js"
  : "https://sandbox-api-pw.izipay.pe/js/v1/checkout.js";

<Script src={SDK_URL} strategy="beforeInteractive" />
```

---

## 11. Variables de entorno (consolidado)

### Backend (`config/settings/base.py`)

```python
# Izipay
IZIPAY_SHOP_ID = env("IZIPAY_SHOP_ID", default="")
IZIPAY_KEY = env("IZIPAY_KEY", default="")  # Bearer token / Public RSA
```

### Frontend (`.env.local`)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_IZIPAY_SDK_URL=https://sandbox-api-pw.izipay.pe/js/v1/checkout.js
NEXT_PUBLIC_IZIPAY_MODE=test  # test|production
NEXT_PUBLIC_IZIPAY_RSA_PUBLIC_KEY=  # opcional: si se quiere validar config local
```

---

## 12. Archivos de la app de referencia (referencias exactas)

### Backend
```
ninja/domains/finanzas/
├── __init__.py
├── admin.py
├── apps.py
├── constants.py               # EstadoOrden
├── permissions.py             # PermisosPagos
├── views.py
├── api/
│   └── pagos.py               # PagosController (3 endpoints)
├── management/commands/
│   └── expire_orders.py       # Expira órdenes pendientes
├── migrations/
│   ├── 0001_initial.py        # Crea OrdenDeCobro y Pago
│   └── 0002_initial.py
├── models/
│   ├── __init__.py
│   ├── orden_cobro.py         # OrdenDeCobro (UUIDModel + TimestampedModel + HistoricalRecords)
│   └── pago.py                # Pago con tipos/métodos
├── schemas/
│   ├── __init__.py
│   └── pago.py                # PagoManualIn, PagoOut, IzipayTokenOut, IzipayConfirmIn
└── services/
    ├── __init__.py
    ├── pago_service.py        # PagoService (registrar_pago, actualizar_saldo_orden, anular_pago)
    └── izipay_service.py      # IzipayService (generar_token_sesion, verificar_y_registrar)
```

### Frontend
```
ninja-front/
├── components/pagos/
│   └── IzipayModal.tsx        # Modal pop-up con new window.Izipay({ config: finalConfig })
└── hooks/finanzas/
    └── usePagoActions.ts      # usePagoActions().registrarPagoManual mutation
```

---

## 13. Plan de adaptación para Salesianos FEST

### 13.1 Diferencias clave con Salesianos FEST

| Concepto | Referencia (centro-de-esparcimiento) | Salesianos FEST |
|----------|--------------------------------------|-----------------|
| Modelo central | `OrdenDeCobro` | `Inscripcion` |
| Contexto | Entradas, reservas, bungalows | Inscripciones deportivas |
| Estados | `EstadoOrden` (5 estados) | `EstadoInscripcionChoices` (8 estados, ya tiene PAGO_PENDIENTE/PAGADA) |
| Monto | `OrdenDeCobro.monto_total` | `Inscripcion` debería tener campo `monto_total` (no existe aún) |
| Relación | `OrdenDeCobro.pagos` | `Inscripcion.pagos` |
| Endpoint | `/api/finanzas/pagos/...` | `/api/pagos/...` |
| Cajero | `Usuario` que registra | `request.auth` (admin) — frontend usa `request.user` para identificar |

### 13.2 Plan de implementación (4 fases SDD)

**Fase 1 — Modelos y migraciones**
- Crear `Pago` y migraciones
- Agregar `monto_total` y FK `pagos` a `Inscripcion`
- Crear `EstadoPago` y `TipoMovimientoDinero` en constantes

**Fase 2 — Servicios backend**
- `PagoService.actualizar_saldo_inscripcion()` (análogo a `actualizar_saldo_orden`)
- `PagoService.registrar_pago()` (análogo)
- `IzipayService.generar_token_sesion()` con `inscripcion_id`
- `IzipayService.verificar_y_registrar()`
- Configurar `settings.IZIPAY_SHOP_ID` y `IZIPAY_KEY`

**Fase 3 — Controllers y schemas**
- `PagoManualIn`, `PagoOut`, `IzipayTokenOut`, `IzipayConfirmIn`
- `PagosController` con 3 endpoints

**Fase 4 — Frontend**
- `IzipayModal.tsx` adaptado para `inscripcion_id`
- `useIniciarPago` hook con TanStack Query
- Conectar botón "Proceder al Pago" en `InscripcionDetailView.tsx`
- Cargar SDK Izipay en `app/layout.tsx`
- Páginas `/pago/exito` y `/pago/fallo`
- Tabla "Mis Pagos" en `/dashboard/pagos`

---

## 14. Riesgos y consideraciones

| Riesgo | Severidad | Mitigación |
|--------|----------|-------------|
| Inscripcion no tiene `monto_total` | CRÍTICA | Agregar migración |
| No existe `OrdenDeCobro` analog en Salesianos | MEDIA | Usar Inscripcion directamente con FK a Pago |
| Izipay sandbox requiere internet | ALTA | Verificar conectividad antes de tests E2E |
| RSA key pública hardcodeada en frontend | BAJA | Mover a `NEXT_PUBLIC_IZIPAY_RSA_PUBLIC_KEY` env var |
| Idempotencia solo por `referencia=transaction_id` | MEDIA | Agregar tabla `WebhookEvent` con constraint unique |
| No hay webhooks reales (solo callback pop-up) | BAJA | Mantener comportamiento de app de referencia |

---

## 15. Lecciones aprendidas de la app de referencia

1. **Patrón `OrdenDeCobro` o equivalente**: Centraliza el dinero en una entidad "folio" que recibe pagos. Para Salesianos FEST, esa entidad es `Inscripcion`.
2. **`metadatos JSONField`**: Almacena toda la respuesta de Izipay para auditoría. Es clave para soporte post-pago.
3. **Simple-history (`HistoricalRecords`)**: Audita cambios en `Pago` y `OrdenDeCobro`. Replicar en Salesianos FEST.
4. **Sanitización de textos**: `_sanitizar_texto` y `sanitizeNamePart` evitan que Izipay rechace la config inicial por caracteres especiales.
5. **Pop-up vs redirect**: La app de referencia usa pop-up (`typeForm: "pop-up"`). Es más simple UX y no requiere redirect handler.
6. **`renderCheckout()` no bloqueante**: Después de `new window.Izipay({ config })` y `.on("payment.response", ...)`, llamar `.renderCheckout()` muestra el modal. El callback se dispara cuando el usuario confirma o rechaza.
7. **Sin webhooks IPN**: La app de referencia NO usa webhooks. Solo callback pop-up. Es válido para Salesianos FEST también.
8. **`code === "00"` = aprobado**: El contrato de respuesta de Izipay siempre usa `code: "00"` para éxito. Cualquier otro código = error.

---

## 16. Checklist de implementación para Salesianos FEST

- [ ] **Backend**: Crear modelo `Pago` (análogo a `centro-de-esparcimiento`)
- [ ] **Backend**: Agregar `monto_total` y `pagos` FK a `Inscripcion`
- [ ] **Backend**: Configurar `IZIPAY_SHOP_ID` y `IZIPAY_KEY` en settings
- [ ] **Backend**: Crear `PagoService` (registrar_pago, actualizar_saldo_inscripcion)
- [ ] **Backend**: Crear `IzipayService` (generar_token_sesion, verificar_y_registrar)
- [ ] **Backend**: Crear schemas `PagoManualIn`, `PagoOut`, `IzipayTokenOut`, `IzipayConfirmIn`
- [ ] **Backend**: Crear `PagosController` con 3 endpoints
- [ ] **Frontend**: Crear `IzipayModal.tsx` (basado en referencia)
- [ ] **Frontend**: Crear `usePagoActions` hook
- [ ] **Frontend**: Cargar SDK Izipay en `app/layout.tsx`
- [ ] **Frontend**: Conectar botón "Proceder al Pago" en `InscripcionDetailView`
- [ ] **Frontend**: Crear páginas `/pago/exito` y `/pago/fallo`
- [ ] **Frontend**: Tabla "Mis Pagos" en `/dashboard/pagos`
- [ ] **Tests**: Unit tests para PagoService, IzipayService
- [ ] **Tests**: Integration tests para los 3 endpoints
- [ ] **Config**: Vars de entorno en `.env.local` (backend + frontend)

---

## 17. Documentos relacionados (de la app de referencia)

### 17.1 `SP_SERVICIO_PAGAR - Parametros.docx`

**Procedimiento:** `SP_SERVICIO_PAGAR`

Stored procedure legacy de la app de referencia para generar el comprobante de pago electrónico (CPE — Boleta/Factura) usado por SUNAT/PERÚ.

| Parámetro | Tipo | Long | Valores | I/O |
|-----------|------|------|---------|-----|
| `p_TipoDocIdentidad` | CHAR | 1 | 1=CIP, 2=RUC, 3=DNI, 4=CARNET EXT, 5=PASAPORTE, 6=EMPRESA EXTRANJERA | INPUT |
| `p_IDCliente` | VARCHAR | 15 | — | INPUT |
| `p_Cliente` | VARCHAR | 100 | — | INPUT |
| `p_IDCapitulo` | CHAR | 2 | Tabla 01 (capítulos) | INPUT |
| `p_TipoCPE` | CHAR | 1 | B=Boleta, F=Factura, C=Nota de Crédito | INPUT |
| `p_SerieCPE` | CHAR | 3 | B08, B11, F08, F11 | INPUT |
| `p_NroRUC` | VARCHAR | 15 | RUC emisor (ej: 20173173181) | INPUT |
| `p_TipoMoneda` | CHAR | 1 | S=Soles, D=Doles | INPUT |
| `p_IDCanalPago` | CHAR | 2 | Tabla 02 | INPUT |
| `p_IDMedioPago` | CHAR | 2 | Tabla 03 | INPUT |
| `p_NroCuentaBanco` | VARCHAR | 20 | — | INPUT |
| `p_FechaOperacion` | CHAR | 10 | AAAA-MM-DD | INPUT |
| `p_NroOperacion` | VARCHAR | 20 | — | INPUT |
| `p_IDUsuario` | VARCHAR | 12 | (ej: AINFANTES) | INPUT |
| `p_Conceptos` | ARRAY | 55 | (ver layout abajo) | INPUT |
| `p_NumeroCPE` | CHAR | 8 | (ej: 00000001) | OUTPUT |

**Layout de `p_Conceptos` (55 chars):**

| Pos | Pos Fin | Long | Campo | Ejemplo |
|-----|---------|------|-------|---------|
| 1 | 2 | 2 | Grupo Concepto | 06 |
| 4 | 5 | 2 | Sub-Grupo Concepto | 08 |
| 7 | 8 | 2 | Concepto | 0608260001 |
| 10 | 19 | 10 | Periodo | 2026-02 |
| 21 | 27 | 7 | (vacío) | (vacío) |
| 29 | 29 | 1 | Frecuencia (U/M/P) | M |
| 31 | 31 | 1 | Tipo Facilidad | N |
| 33 | 34 | 2 | Nro Facilidad | 00 |
| 36 | 36 | 1 | Afecto IGV (0/1) | 0 |
| 38 | 38 | 1 | Estado (I/A) | I |
| 40 | 40 | 1 | Tipo Moneda (S/D) | S |
| 42 | 44 | 3 | Unidades | 001 |
| 46 | 55 | 10 | Precio Unitario | 0000002500 |

**Estructura visual:**

```
NN-NN-NN-NNNNNNNNNN-AAAA-MM-X-X-00-X-X-X-NNN-NNNNNNNNNN
```

### 17.2 `SP_PROCESAR_PAGOS - Parametros.docx`

**Procedimiento:** `SP_PROCESAR_PAGOS`

Stored procedure para procesar un pago y emitir el comprobante.

| Parámetro | Tipo | Long | Dec | Valores | I/O |
|-----------|------|------|-----|---------|-----|
| `P_TipoDocIdentidad` | CHAR | 1 | — | 1=CIP, 2=RUC, 3=DNI, 4=CARNET EXT, 5=PASAPORTE | INPUT |
| `NroDocIdentidad` | VARCHAR | 15 | — | — | INPUT |
| `p_TipoCPE` | CHAR | 1 | — | B=Boleta, F=Factura, C=Nota de Crédito | INPUT |
| `p_NroRUC` | VARCHAR | 15 | — | — | INPUT |
| `p_TipoMoneda` | CHAR | 1 | — | S=Soles, D=Dolares | INPUT |
| `p_Total` | NUMERIC | 10 | 2 | ej: 25.00 | INPUT |
| `p_CodigoComercio` | VARCHAR2 | 20 | — | (de Izipay) | INPUT |
| `p_NroPedido` | VARCHAR2 | 15 | — | (de Izipay) | INPUT |
| `ArrConceptos` | ARRAY | 55 | — | (ver layout abajo) | INPUT |
| — | — | — | — | — | OUTPUT CURSOR |

**Layout de `ArrConceptos` (55 chars):**

| Pos | Pos Fin | Long | Campo | Ejemplo |
|-----|---------|------|-------|---------|
| 1 | 2 | 2 | Grupo Concepto | 06 |
| 3 | 4 | 2 | Sub-Grupo Concepto | 08 |
| 5 | 14 | 10 | Concepto | 0608260001 |
| 15 | 15 | 1 | Tipo Facilidad | N |
| 16 | 17 | 2 | Nro Facilidad | 00 |
| 18 | 23 | 6 | Periodo - Cuota - Desde | AAAAMM |
| 24 | 29 | 6 | Periodo - Cuota - Hasta | AAAAMM |
| 30 | 33 | 4 | Unidades | 0001 |
| 34 | 34 | 1 | Tipo Moneda | S |
| 35 | 44 | 10 | Sub-Total x Unidad | 0000002500 |
| 45 | 54 | 10 | Sub-Total | 0000002500 |
| 55 | 55 | 1 | Signo (+ o -) | + |

**Cursor de salida:**

| Campo | Tipo | Valores |
|-------|------|---------|
| `TIPO_CPE` | CHAR | B=Boleta, F=Factura |
| `SERIE_CPE` | CHAR | B08, F08 |
| `FOLIO_CPE` | CHAR | 00000001 |

### 17.3 Procedimiento `SP_FACTURACION_ELECTRONICA_V3`

Invocado por `SP_PROCESAR_PAGOS` después del pago. Parámetros:
- `v_TipoDocumento`: enviar `TIPO_CPE` retornado por `SP_PROCESAR_PAGOS`
- `v_NroSerie`: enviar `SERIE_CPE`
- `v_NroDocumento`: enviar `FOLIO_CPE`

---

## 18. Plan de implementación para Salesianos FEST

### 18.1 Tabla de adaptación (resumen)

| Aspecto | Referencia (centro-de-esparcimiento) | Salesianos FEST |
|---|---|---|
| Entidad madre | `OrdenDeCobro` | `Inscripcion` |
| Campo monto | `orden.monto_total` | `inscripcion.paquete.precio_total` |
| Campo saldo | `orden.saldo_pendiente` | Fijo = `paquete.precio_total` (sin pagos parciales v1) |
| Persona que paga | `orden.cliente` (User) | `inscripcion.responsable` (Persona → Usuario) |
| Estado nuevo en Inscripción | No aplica | `PENDIENTE → PAGO_PENDIENTE → PAGADA` |
| Routing API backend | `/api/finanzas/pagos/...` | `/api/pagos/...` |
| Módulo backend | `domains/finanzas/` (legacy) | `modules/pagos/` (nuevo, limpio) |
| Feature frontend | `components/pagos/` (legacy) | `src/features/pagos/` (nuevo) |

### 18.2 Árbol completo de archivos backend a crear

```
backend/modules/pagos/
├── __init__.py
├── apps.py
├── admin.py                        # Admin Django de Pago
├── di.py                           # Dependency Injection module
├── domain/
│   ├── __init__.py
│   ├── constants.py                # EstadoPago (opcional)
│   ├── permissions.py              # PermisosPagos (gestionar, ver_todos)
│   ├── models/
│   │   ├── __init__.py             # Exporta Pago, TipoMovimientoDinero, MetodoPago
│   │   └── pago.py                 # Modelo Pago + enums + HistoricalRecords
│   └── services/
│       ├── __init__.py
│       ├── pago_service.py         # Lógica contable
│       └── izipay_service.py       # Integración Izipay
├── presentation/
│   ├── __init__.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── pago_schema.py          # PagoManualIn, PagoOut, IzipayTokenOut, IzipayConfirmIn
│   └── controllers/
│       ├── __init__.py
│       └── pagos_controller.py     # 3 endpoints
├── migrations/
│   ├── __init__.py
│   └── 0001_initial.py             # Crea tabla Pago + FK
└── tests/
    ├── __init__.py
    ├── test_pago_service.py
    ├── test_izipay_service.py
    └── test_pagos_controller.py
```

### 18.3 Archivos backend a modificar

| Path | Cambio |
|---|---|
| `backend/config/settings/base.py` | Agregar `IZIPAY_SHOP_ID`, `IZIPAY_KEY`, `IZIPAY_API_URL` |
| `backend/config/api.py` | Registrar `PagosController` |
| `backend/modules/inscripciones/domain/models/inscripcion.py` | Agregar `monto_pagado` Decimal + propiedad `monto_total` |
| `backend/modules/inscripciones/migrations/XXXX_agregar_monto_pagado.py` | Nueva migración |

### 18.4 Cambios en modelo Inscripcion

```python
# Inscripcion (modificación)
monto_pagado = models.DecimalField(
    max_digits=10, decimal_places=2, default=Decimal("0.00"),
    help_text="Suma de Pago.monto (INGRESO) - Pago.monto (EGRESO) para esta inscripción.",
)

@property
def monto_total(self) -> Decimal:
    return self.paquete.precio_total

@property
def esta_pagada(self) -> bool:
    return self.estado == EstadoInscripcionChoices.PAGADA
```

### 18.5 Árbol completo de archivos frontend a crear

```
frontend/src/features/pagos/
├── components/
│   └── IzipayModal.tsx             # Pop-up Izipay (sanitizers del patrón)
├── hooks/
│   ├── useIniciarPago.ts          # Hook: preparar token Izipay
│   └── usePagoActions.ts           # Hook: confirmar pago, registrar manual
├── services/
│   └── pago.service.ts             # Llamadas a /api/pagos/*
└── schemas/
    └── pago.schema.ts             # Tipos TypeScript

frontend/src/app/pago/
├── exito/
│   └── page.tsx                    # Pago exitoso (refetch + toast)
└── fallo/
    └── page.tsx                    # Pago fallido (mensaje + CTA reintentar)
```

### 18.6 Archivos frontend a modificar

| Path | Cambio |
|---|---|
| `frontend/src/app/layout.tsx` | Cargar SDK Izipay con `<Script strategy="beforeInteractive" />` |
| `frontend/src/features/inscripciones/views/InscripcionDetailView.tsx` | Botón "Proceder al Pago" abre `IzipayModal`, onSuccess hace refetch |

### 18.7 Variables de entorno

**Backend (`backend/.env`):**

```env
IZIPAY_SHOP_ID=tu_shop_id
IZIPAY_KEY=tu_api_key
IZIPAY_API_URL=https://sandbox-api-pw.izipay.pe/security/v1/Token/Generate
```

**Frontend (`frontend/.env.local`):**

```env
NEXT_PUBLIC_IZIPAY_SDK_URL=https://sandbox-checkout.izipay.pe/payments/v1/js/index.js
```

---

## 19. Fases SDD (4 fases con cronograma)

### Fase 1: Estructura y Migraciones (Estimación: 1 día)

**Tareas:**
1. Crear árbol `modules/pagos/`
2. Crear modelo `Pago` + enums
3. Modificar `Inscripcion` (agregar `monto_pagado` + propiedad)
4. Crear migración `0001_initial.py` (tabla Pago)
5. Crear migración para `monto_pagado`
6. Crear `PermisosPagos`
7. Registrar en `config/settings/base.py` (`LOCAL_APPS`)
8. Registrar controller en `config/api.py`

**Criterio de done:**
- `python manage.py showmigrations pagos` aplicado
- `python manage.py showmigrations inscripciones` muestra la nueva migración
- `curl /api/pagos/docs` retorna OpenAPI

### Fase 2: Servicios y Controllers (Estimación: 1.5 días)

**Tareas:**
1. `PagoService.calcular_monto_pago_inscripcion()`
2. `PagoService.registrar_pago()` con validación de estado
3. `PagoService.obtener_resumen_pago()`
4. `IzipayService._sanitizar_texto()` (sanitizadores)
5. `IzipayService.generar_token_sesion()` (HTTP real a Izipay)
6. `IzipayService.verificar_y_registrar()` (idempotencia + actualizar Inscripcion)
7. Schemas en `pago_schema.py`
8. `PagosController` con 3 endpoints
9. Tests unitarios

**Criterio de done:**
- `pytest modules/pagos/tests/ -v` pasa
- `GET /api/pagos/izipay/preparar/{id}` retorna token
- `POST /api/pagos/izipay/confirmar` registra pago y actualiza Inscripcion

### Fase 3: Frontend Modal + Conexión (Estimación: 1.5 días)

**Tareas:**
1. Crear `frontend/src/features/pagos/` con estructura completa
2. `IzipayModal.tsx` con sanitizadores del patrón
3. `useIniciarPago.ts` y `usePagoActions.ts`
4. `pago.service.ts` con llamadas API
5. `pago.schema.ts` con tipos
6. Modificar `frontend/src/app/layout.tsx` para cargar SDK
7. Modificar `InscripcionDetailView.tsx` (botón + modal + refetch)
8. Crear `pago/exito/page.tsx` y `pago/fallo/page.tsx`
9. `.env.local` con variables

**Criterio de done:**
- Botón "Proceder al Pago" abre modal
- SDK Izipay carga sin errores
- Flujo completo (preparar → pop-up → confirmar) funciona

### Fase 4: Validación E2E (Estimación: 0.5 días)

**Tareas:**
1. Tests de integración controller
2. Probar transición `PAGO_PENDIENTE → PAGADA`
3. Probar pago duplicado (idempotencia)
4. Probar inscripción ya pagada (no abre modal)
5. Documentar en `.env.example`

**Criterio de done:**
- `pytest modules/pagos/ modules/inscripciones/ -v` 100%
- Flujo manual probado: inscribir → pagar → ver `PAGADA`

---

## 20. Adaptación a Salesianos FEST: facturación electrónica

### 20.1 Tablas y modelos que NO existen en Salesianos FEST

Los modelos legacy de facturación electrónica no son necesarios para la implementación inicial. Solo sirven como **referencia operativa**:

| Tabla legacy | Equivalente en Salesianos |
|--------------|---------------------------|
| Tabla 01 (Capítulos) | No aplica — solo categorías deportivas |
| Tabla 02 (Canal de pago) | `MetodoPago` enum |
| Tabla 03 (Medio de pago) | `MetodoPago` enum + Izipay `payMethod` |
| Tabla 04 (Servicio) | `Paquete` model |
| p_Conceptos array | `Inscripcion.equipos[]` con `disciplina_id` |
| p_SerieCPE (B08, B11, F08, F11) | No aplica (facturación electrónica futura) |

### 20.2 Lo que SÍ se debe crear en Salesianos FEST

**Backend (tablas reales):**

```
Pago
├─ id (UUID PK)
├─ inscripcion (FK Inscripcion, on_delete=PROTECT)
├─ responsable (FK Usuario, on_delete=PROTECT) — quien registró
├─ tipo (ENUM: INGRESO, EGRESO)
├─ monto (Decimal)
├─ metodo (ENUM: EFECTIVO, YAPE_PLIN, TARJETA, TRANSFERENCIA, OTRO)
├─ referencia (CharField — transactionId de Izipay o nro Yape)
├─ metadatos (JSONField — respuesta completa de Izipay)
├─ tipo_comprobante (CharField blank — para futura integración Sunat)
├─ serie_correlativo (CharField blank — para futura integración Sunat)
├─ created_at, updated_at
└─ Meta: ordering ['-created_at']

Inscripcion (modificación)
├─ + monto_total (Decimal) — derivado del paquete
├─ + saldo_pendiente (Decimal) — default 0.00
├─ + esta_pagada (Boolean) — default False
└─ + pagos (related_name='pagos' en Pago)
```

### 20.3 Plantillas `p_Conceptos` adaptadas a Salesianos FEST

Para la implementación inicial, NO se implementa facturación electrónica. El campo `metadatos JSONField` en `Pago` guarda toda la respuesta cruda de Izipay para auditoría. Cuando se integre Sunat/PERÚ en el futuro, las plantillas `p_Conceptos` se adaptarán a:

- **Grupo Concepto**: `06` (Servicios deportivos)
- **Sub-Grupo**: `08` (Inscripciones)
- **Concepto**: `06{paquete_tipo_id}{anio}001` (ej: 0608260001)
- **Unidades**: `cantidad de equipos`
- **Precio Unitario**: `paquete.precio_promocional || paquete.precio_regular`

> **Nota (2026-09-21):** los parámetros CIP y capítulo del `SP_SERVICIO_PAGAR` / `SP_PROCESAR_PAGOS` son específicos de un dominio SUNAT/facturación electrónica con colegiados. **No aplican** a Salesianos FEST. Esta aplicación no tiene colegiados ni facturación electrónica SUNAT.

---

## 21. Conclusión

El módulo de pagos Izipay de la app de referencia (`centro-de-esparcimiento`) está **completo y validado en producción**. Su patrón central es:

```
OrdenDeCobro (folio maestro)
    ↓ (FK 1:N)
Pago[] (transacciones individuales, IGRESO/EGRESO)
    ↓
Izipay Web Core 2.0 (pop-up) → callback → verificación → registro idempotente
```

Para Salesianos FEST, el patrón se adapta cambiando `OrdenDeCobro` por `Inscripcion` y agregando los campos necesarios a `Inscripcion` (`monto_total`, `monto_pagado`, `esta_pagada`).

El plan completo (4 fases SDD, ~4.5 días) está documentado en la sección 19. La sección 18 tiene el árbol completo de archivos y los cambios en archivos existentes.

Verificación:
- `npx tsc --noEmit` limpio.
- `python -m pytest modules/inscripciones/ modules/usuarios/` → 84/84 verde.
