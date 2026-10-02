"""
IzipayPresenter — transforms domain result objects into HTTP schemas.

Transforms only — presenter does NOT query the DB.
"""
from modules.pagos.domain.models import IzipayTransaccion
from modules.pagos.domain.schemas.result import IzipayPrepareResult, IzipayConfirmResult
from modules.pagos.presentation.schemas.pago_schema import (
    IzipayPrepareOut,
    IzipayConfirmOut,
    IzipayTransaccionOut,
)


class IzipayPresenter:
    """Transforms Izipay Perú domain results and models into HTTP output schemas."""

    # ── Prepare ────────────────────────────────────────────────────────────────

    @staticmethod
    def present_prepare(result: IzipayPrepareResult) -> IzipayPrepareOut:
        """
        Transform IzipayPrepareResult into IzipayPrepareOut.

        The result contains the token and merchant_code needed by the frontend
        Web Core 2.0 SDK: checkout.LoadForm({ authorization: token,
                                                  merchantCode, orderNumber,
                                                  amount, currency, transactionId })
        """
        return IzipayPrepareOut(
            transaction_id=result.transaction_id,
            order_number=result.order_number,
            token=result.token,
            merchant_code=result.merchant_code,
            amount=result.amount,
            currency=result.currency,
            buyer_email=result.buyer_email,
            buyer_name=result.buyer_name,
            buyer_surname=result.buyer_surname,
        )

    # ── Confirm ──────────────────────────────────────────────────────────────

    @staticmethod
    def present_confirm(result: IzipayConfirmResult) -> IzipayConfirmOut:
        """Transform IzipayConfirmResult into IzipayConfirmOut."""
        return IzipayConfirmOut(
            transaction_id=result.transaction_id,
            success=result.success,
            status=result.status,
            response_code=result.response_code,
            response_message=result.response_message,
            metodo_pago=result.metodo_pago,
            already_confirmed=result.already_confirmed,
        )

    # ── Transaccion ─────────────────────────────────────────────────────────

    @staticmethod
    def present_transaccion(tx: IzipayTransaccion) -> IzipayTransaccionOut:
        """Transform an IzipayTransaccion model instance into IzipayTransaccionOut."""
        return IzipayTransaccionOut(
            id=str(tx.id),
            inscripcion_id=str(tx.inscripcion_id),
            transaction_id=tx.transaction_id,
            order_number=tx.order_number,
            amount=tx.amount,
            currency=tx.currency,
            status=tx.status,
            response_code=tx.response_code,
            response_message=tx.response_message,
            metodo_pago=tx.metodo_pago,
            created_at=tx.created_at.isoformat(),
            updated_at=tx.updated_at.isoformat(),
        )
