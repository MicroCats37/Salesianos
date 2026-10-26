"""Paquete selector — read-only queries for paquetes."""
from datetime import date
from typing import List, Optional

from django.db.models import Prefetch

from ..models import Paquete, PaqueteDisciplina, PaquetePrecio, PaqueteBeneficio
from ..results.catalogo_results import (
    PaqueteResult,
    PaqueteListResult,
    PaquetePrecioResult,
    PaqueteBeneficioResult,
    PaqueteDisciplinaResult,
)


class PaqueteSelector:
    """Queries for Paquete entities."""

    @staticmethod
    def get_activos() -> List[PaqueteListResult]:
        """
        Return active paquetes as a flat list (for catalog listing).
        Includes the current PREVENTA and REGULAR prices if available.
        """
        today = date.today()
        paquetes = (
            Paquete.objects.filter(activo=True)
            .select_related("evento")
            .prefetch_related(
                Prefetch(
                    "precios",
                    queryset=PaquetePrecio.objects.filter(activo=True).order_by("etapa"),
                ),
                Prefetch(
                    "beneficios",
                    queryset=PaqueteBeneficio.objects.all(),
                ),
                Prefetch(
                    "paquete_disciplinas",
                    queryset=PaqueteDisciplina.objects.select_related(
                        "disciplina"
                    ).order_by("created_at"),
                ),
            )
            .order_by("evento__nombre", "nombre")
        )

        results = []
        for p in paquetes:
            precio_preventa = None
            precio_regular = None
            tiene_fiesta = False

            for precio in p.precios.all():
                if precio.etapa == "PREVENTA":
                    precio_preventa = precio.precio_unitario
                elif precio.etapa == "REGULAR":
                    precio_regular = precio.precio_unitario

            for beneficio in p.beneficios.all():
                if beneficio.tipo == "FIESTA":
                    tiene_fiesta = True
                    break

            tiene_box = any(b.tipo == "BOX" for b in p.beneficios.all())
            tiene_cerveza = any(b.tipo == "CERVEZA" for b in p.beneficios.all())

            # Build disciplinas_resumen and the canonical disciplinas[] list
            # from the prefetched paquete_disciplinas (no extra queries).
            paquete_disciplinas = list(p.paquete_disciplinas.all())
            disciplinas_resumen = [
                pd.disciplina.sigla for pd in paquete_disciplinas
            ]
            disciplinas = [
                PaqueteDisciplinaResult(
                    disciplina_id=str(pd.disciplina_id),
                    disciplina_nombre=pd.disciplina.nombre,
                    disciplina_sigla=pd.disciplina.sigla,
                    min_jugadores=pd.disciplina.min_jugadores,
                    max_jugadores=pd.disciplina.max_jugadores,
                )
                for pd in paquete_disciplinas
            ]

            # Build full beneficios[] and precios[] from prefetched relations
            beneficios = [
                PaqueteBeneficioResult(
                    tipo=b.tipo,
                    cantidad=b.cantidad,
                    alcance=b.alcance,
                    modo_calculo=b.modo_calculo,
                )
                for b in p.beneficios.all()
            ]
            precios = [
                PaquetePrecioResult(
                    etapa=precio.etapa,
                    precio_unitario=precio.precio_unitario,
                    vigente_desde=precio.vigente_desde,
                    vigente_hasta=precio.vigente_hasta,
                )
                for precio in p.precios.all()
            ]

            results.append(
                PaqueteListResult(
                    id=str(p.id),
                    evento_id=str(p.evento_id),
                    nombre=p.nombre,
                    descripcion=p.descripcion,
                    tipo=p.tipo,
                    modo_disciplinas=p.modo_disciplinas,
                    cantidad_disciplinas=p.cantidad_disciplinas,
                    cantidad_minima_compra=p.minimo_compra_inicial,
                    cantidad_maxima_equipos=p.cantidad_disciplinas,
                    precio_preventa=precio_preventa,
                    precio_regular=precio_regular,
                    tiene_fiesta=tiene_fiesta,
                    tiene_box=tiene_box,
                    tiene_cerveza=tiene_cerveza,
                    disciplinas_resumen=disciplinas_resumen,
                    disciplinas=disciplinas,
                    beneficios=beneficios,
                    precios=precios,
                )
            )
        return results

    @staticmethod
    def get_by_id(paquete_id: str) -> Optional[PaqueteResult]:
        """
        Return a paquete by ID with all nested prices, benefits, and disciplines.
        """
        try:
            p = (
                Paquete.objects.select_related("evento")
                .prefetch_related(
                    Prefetch(
                        "precios",
                        queryset=PaquetePrecio.objects.filter(activo=True).order_by("etapa"),
                    ),
                    Prefetch(
                        "beneficios",
                        queryset=PaqueteBeneficio.objects.all(),
                    ),
                    Prefetch(
                        "paquete_disciplinas",
                        queryset=PaqueteDisciplina.objects.select_related("disciplina"),
                    ),
                )
                .get(id=paquete_id)
            )
        except Paquete.DoesNotExist:
            return None

        precios = [
            PaquetePrecioResult(
                etapa=precio.etapa,
                precio_unitario=precio.precio_unitario,
                vigente_desde=precio.vigente_desde,
                vigente_hasta=precio.vigente_hasta,
            )
            for precio in p.precios.all()
        ]

        beneficios = [
            PaqueteBeneficioResult(
                tipo=beneficio.tipo,
                cantidad=beneficio.cantidad,
                alcance=beneficio.alcance,
                modo_calculo=beneficio.modo_calculo,
            )
            for beneficio in p.beneficios.all()
        ]

        disciplinas = [
            PaqueteDisciplinaResult(
                disciplina_id=str(pd.disciplina_id),
                disciplina_nombre=pd.disciplina.nombre,
                disciplina_sigla=pd.disciplina.sigla,
            )
            for pd in p.paquete_disciplinas.all()
        ]

        return PaqueteResult(
            id=str(p.id),
            evento_id=str(p.evento_id),
            nombre=p.nombre,
            descripcion=p.descripcion,
            tipo=p.tipo,
            modo_disciplinas=p.modo_disciplinas,
            cantidad_disciplinas=p.cantidad_disciplinas,
            minimo_compra_inicial=p.minimo_compra_inicial,
            precios=precios,
            beneficios=beneficios,
            disciplinas=disciplinas,
        )
