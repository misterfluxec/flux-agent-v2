from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from decimal import Decimal
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

class LedgerService:
    """
    Sprint H3: Operational Financial Ledger.
    Implements double-entry ledger restricted to 4 critical operations for Beta:
    payment_received, refund_issued, fee_applied, adjustment.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_payment_received(self, tenant_id: str, customer_id: str, amount: Decimal, currency: str, reference_id: str) -> None:
        """
        Records a successful payment from a customer.
        Credit increases the customer's balance or offsets an invoice.
        """
        await self._insert_entry(
            tenant_id=tenant_id,
            customer_id=customer_id,
            entry_type="payment_received",
            debit=Decimal('0.00'),
            credit=amount,
            currency=currency,
            reference_type="order",
            reference_id=reference_id
        )

    async def record_refund_issued(self, tenant_id: str, customer_id: str, amount: Decimal, currency: str, reference_id: str) -> None:
        """
        Records a refund back to the customer.
        Debit reduces the customer's balance.
        """
        await self._insert_entry(
            tenant_id=tenant_id,
            customer_id=customer_id,
            entry_type="refund_issued",
            debit=amount,
            credit=Decimal('0.00'),
            currency=currency,
            reference_type="refund",
            reference_id=reference_id
        )

    async def record_fee_applied(self, tenant_id: str, customer_id: str, amount: Decimal, currency: str, reference_id: str) -> None:
        """
        Records a fee (e.g. late fee, service fee) charged to the customer.
        Debit increases what the customer owes.
        """
        await self._insert_entry(
            tenant_id=tenant_id,
            customer_id=customer_id,
            entry_type="fee_applied",
            debit=amount,
            credit=Decimal('0.00'),
            currency=currency,
            reference_type="fee",
            reference_id=reference_id
        )

    async def record_adjustment(self, tenant_id: str, customer_id: str, amount: Decimal, currency: str, is_credit: bool, reference_id: str) -> None:
        """
        Records a manual adjustment to the customer's account.
        """
        await self._insert_entry(
            tenant_id=tenant_id,
            customer_id=customer_id,
            entry_type="adjustment",
            debit=Decimal('0.00') if is_credit else amount,
            credit=amount if is_credit else Decimal('0.00'),
            currency=currency,
            reference_type="adjustment",
            reference_id=reference_id
        )

    async def get_customer_balance(self, tenant_id: str, customer_id: str, currency: str) -> Decimal:
        """
        Fetches the real-time balance from the materialized view.
        Positive means the customer has credit, negative means they owe money.
        """
        stmt = text("""
            SELECT current_balance 
            FROM customer_balances 
            WHERE tenant_id = :tenant_id AND customer_id = :customer_id AND currency = :currency
        """)
        result = await self.db.execute(stmt, {
            "tenant_id": tenant_id, 
            "customer_id": customer_id, 
            "currency": currency
        })
        row = result.fetchone()
        return row[0] if row else Decimal('0.00')

    async def _insert_entry(self, tenant_id: str, customer_id: str, entry_type: str, debit: Decimal, credit: Decimal, currency: str, reference_type: str, reference_id: str):
        stmt = text("""
            INSERT INTO financial_ledger_entries 
            (tenant_id, customer_id, entry_type, debit, credit, currency, reference_type, reference_id)
            VALUES 
            (:tenant_id, :customer_id, :entry_type, :debit, :credit, :currency, :reference_type, :reference_id)
        """)
        await self.db.execute(stmt, {
            "tenant_id": tenant_id,
            "customer_id": customer_id,
            "entry_type": entry_type,
            "debit": debit,
            "credit": credit,
            "currency": currency,
            "reference_type": reference_type,
            "reference_id": reference_id
        })
        logger.info(f"[Ledger] Recorded {entry_type} for customer {customer_id}: D={debit} C={credit} {currency}")
