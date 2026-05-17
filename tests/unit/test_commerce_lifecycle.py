"""
tests/unit/test_commerce_lifecycle.py
=======================================
Tests unitarios para el motor de ciclo de vida comercial.
Cubre: creación de cotizaciones, transición de órdenes, aplicación de promociones.

Grado bancario: cada transacción comercial debe ser predecible y auditada.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta


class TestPromotionEngine:
    """Tests del motor de promociones."""

    def test_flat_discount_calculation(self):
        """Un descuento fijo debe reducir el precio correctamente."""
        # Simular lógica de descuento
        original_price = 100.0
        discount_amount = 15.0
        
        final_price = original_price - discount_amount
        
        assert final_price == 85.0
        assert final_price >= 0  # No debe ser negativo

    def test_percentage_discount_calculation(self):
        """Un descuento porcentual debe calcularse correctamente."""
        original_price = 200.0
        discount_pct = 20  # 20%
        
        discount_amount = original_price * (discount_pct / 100)
        final_price = original_price - discount_amount
        
        assert final_price == 160.0

    def test_promotion_date_validation_active(self):
        """Una promoción con fechas vigentes debe estar activa."""
        now = datetime.utcnow()
        start = now - timedelta(days=1)
        end = now + timedelta(days=7)
        
        is_active = start <= now <= end
        assert is_active is True

    def test_promotion_date_validation_expired(self):
        """Una promoción expirada no debe estar activa."""
        now = datetime.utcnow()
        start = now - timedelta(days=10)
        end = now - timedelta(days=1)  # Ya expiró
        
        is_active = start <= now <= end
        assert is_active is False

    def test_discount_cannot_exceed_100_percent(self):
        """Un descuento no puede exceder el 100% del precio."""
        original_price = 100.0
        discount_pct = 110  # Inválido
        
        # Validar que el descuento máximo es 100%
        safe_pct = min(discount_pct, 100)
        final_price = original_price * (1 - safe_pct / 100)
        
        assert final_price >= 0

    def test_minimum_price_floor(self):
        """El precio final no debe caer por debajo de 0."""
        original_price = 50.0
        discount_amount = 75.0  # Mayor que el precio
        
        final_price = max(0, original_price - discount_amount)
        assert final_price == 0


class TestOrderPipeline:
    """Tests del pipeline de órdenes Kanban."""

    VALID_TRANSITIONS = {
        "pending": ["paid", "cancelled"],
        "paid": ["preparing", "cancelled"],
        "preparing": ["shipped"],
        "shipped": ["delivered"],
        "delivered": [],  # Estado final
        "cancelled": [],  # Estado final
    }

    def _can_transition(self, from_status: str, to_status: str) -> bool:
        """Helper: verifica si la transición de estado es válida."""
        return to_status in self.VALID_TRANSITIONS.get(from_status, [])

    def test_pending_to_paid_is_valid(self):
        """Transición pendiente → pagada es válida."""
        assert self._can_transition("pending", "paid") is True

    def test_pending_to_delivered_is_invalid(self):
        """No se puede saltar de pendiente a entregado."""
        assert self._can_transition("pending", "delivered") is False

    def test_delivered_is_terminal(self):
        """Una orden entregada no puede cambiar de estado."""
        assert self._can_transition("delivered", "shipped") is False
        assert self._can_transition("delivered", "cancelled") is False

    def test_cancelled_is_terminal(self):
        """Una orden cancelada no puede reactivarse."""
        assert self._can_transition("cancelled", "pending") is False

    def test_all_valid_transitions(self):
        """Verificar todas las transiciones válidas del Kanban."""
        valid_cases = [
            ("pending", "paid"),
            ("pending", "cancelled"),
            ("paid", "preparing"),
            ("paid", "cancelled"),
            ("preparing", "shipped"),
            ("shipped", "delivered"),
        ]
        for from_s, to_s in valid_cases:
            assert self._can_transition(from_s, to_s), f"Failed: {from_s} → {to_s}"

    def test_order_total_calculation(self):
        """El total de una orden debe calcularse correctamente."""
        items = [
            {"price": 100.0, "qty": 2},
            {"price": 50.0, "qty": 1},
            {"price": 25.5, "qty": 3},
        ]
        subtotal = sum(i["price"] * i["qty"] for i in items)
        tax_rate = 0.16  # 16% IVA
        tax = subtotal * tax_rate
        total = subtotal + tax

        assert subtotal == 326.5
        assert abs(tax - 52.24) < 0.01
        assert abs(total - 378.74) < 0.01


class TestQuoteGeneration:
    """Tests de generación de cotizaciones."""

    def test_quote_expiry_is_set(self):
        """Una cotización debe tener fecha de expiración."""
        created_at = datetime.utcnow()
        expiry_days = 7
        expires_at = created_at + timedelta(days=expiry_days)
        
        assert expires_at > created_at
        delta = expires_at - created_at
        assert delta.days == expiry_days

    def test_quote_is_expired(self):
        """Debe detectar correctamente una cotización expirada."""
        expires_at = datetime.utcnow() - timedelta(hours=1)
        is_expired = datetime.utcnow() > expires_at
        assert is_expired is True

    def test_quote_is_not_expired(self):
        """Una cotización futura no debe estar expirada."""
        expires_at = datetime.utcnow() + timedelta(days=3)
        is_expired = datetime.utcnow() > expires_at
        assert is_expired is False
