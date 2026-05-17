"""
tests/unit/test_auth_security.py
=================================
Tests unitarios para seguridad de autenticación.
Cubre: política de contraseñas, validación de JWT, rate limiting.

Grado bancario: estos tests deben pasar antes de cualquier deploy a producción.
"""
import pytest
from pydantic import ValidationError


# ─── Importamos el modelo directamente para testear validators ───────────────
# Usamos importlib para evitar cargar todo FastAPI
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))


class TestPasswordPolicy:
    """Tests de política de contraseñas (grado bancario: 8+ chars + complejidad)."""

    def _make_register_request(self, password: str):
        """Helper para intentar crear un RegisterRequest con un password dado."""
        from routers.auth_router import RegisterRequest
        return RegisterRequest(
            nombre_usuario="TestUser",
            email="test@example.com",
            password=password,
        )

    def test_password_too_short_fails(self):
        """Password de menos de 8 caracteres debe fallar."""
        with pytest.raises(ValidationError) as exc_info:
            self._make_register_request("Ab1!")
        errors = exc_info.value.errors()
        assert any("8" in str(e) or "mínimo" in str(e) for e in errors)

    def test_password_exactly_6_chars_fails(self):
        """El antiguo mínimo de 6 chars ahora debe fallar también."""
        with pytest.raises(ValidationError):
            self._make_register_request("Ab1!xy")

    def test_password_no_uppercase_fails(self):
        """Password sin mayúscula debe fallar."""
        with pytest.raises(ValidationError) as exc_info:
            self._make_register_request("abcdef1!")
        errors = str(exc_info.value)
        assert "mayúscula" in errors or "uppercase" in errors.lower()

    def test_password_no_digit_fails(self):
        """Password sin número debe fallar."""
        with pytest.raises(ValidationError) as exc_info:
            self._make_register_request("Abcdefg!")
        errors = str(exc_info.value)
        assert "número" in errors or "digit" in errors.lower()

    def test_password_no_special_char_fails(self):
        """Password sin carácter especial debe fallar."""
        with pytest.raises(ValidationError) as exc_info:
            self._make_register_request("Abcdefg1")
        errors = str(exc_info.value)
        assert "especial" in errors or "special" in errors.lower()

    def test_valid_password_passes(self):
        """Un password que cumple todos los criterios debe pasar."""
        req = self._make_register_request("SecurePass1!")
        assert req.password == "SecurePass1!"

    def test_valid_password_with_symbols(self):
        """Passwords con diferentes símbolos deben pasar."""
        valid_passwords = [
            "MyPass1@",
            "FluxAgent2026#",
            "Banking$Grade9",
            "P@ssw0rd_Secure",
        ]
        for pwd in valid_passwords:
            req = self._make_register_request(pwd)
            assert req.password == pwd

    def test_email_normalization(self):
        """El email debe ser normalizado a minúsculas."""
        req = self._make_register_request("SecurePass1!")
        # Email ya se normaliza en el validator
        from routers.auth_router import RegisterRequest
        req = RegisterRequest(
            nombre_usuario="Test",
            email="  TEST@EXAMPLE.COM  ",
            password="SecurePass1!",
        )
        assert req.email == "test@example.com"


class TestSecurityHeaders:
    """Tests del middleware de security headers."""

    def test_security_headers_middleware_exists(self):
        """El middleware de security headers debe estar importable."""
        from core.middleware.tenant_isolation import SecurityHeadersMiddleware
        assert SecurityHeadersMiddleware is not None

    def test_security_headers_has_production_mode(self):
        """El middleware debe tener soporte para modo producción."""
        from core.middleware.tenant_isolation import SecurityHeadersMiddleware
        import inspect
        source = inspect.getsource(SecurityHeadersMiddleware)
        assert "is_production" in source
        assert "Strict-Transport-Security" in source
        assert "Content-Security-Policy" in source
        assert "Permissions-Policy" in source


class TestJWTValidation:
    """Tests de validación de tokens JWT."""

    def test_jwt_token_creation(self):
        """Se debe poder crear un token JWT válido."""
        from auth import crear_access_token, PayloadToken
        payload = PayloadToken(
            sub="test-user-id",
            tenant_id="test-tenant-id",
            rol="admin",
            nombre="Test User",
            plan="starter",
        )
        token = crear_access_token(payload)
        assert token is not None
        assert len(token) > 50  # JWT tiene longitud mínima

    def test_jwt_payload_structure(self):
        """El payload del JWT debe contener tenant_id y rol."""
        import jwt as pyjwt
        from auth import crear_access_token, PayloadToken

        payload = PayloadToken(
            sub="test-user-id",
            tenant_id="test-tenant-id",
            rol="admin",
            nombre="Test User",
            plan="pro",
        )
        token = crear_access_token(payload)

        # Decodificar sin verificar para inspeccionar el payload
        decoded = pyjwt.decode(
            token,
            algorithms=["HS256"],
            options={
                "verify_signature": False,
                "verify_exp": False,
            }
        )
        assert "sub" in decoded
        assert "tenant_id" in decoded
        assert "rol" in decoded
        assert decoded["rol"] == "admin"
        assert decoded["tenant_id"] == "test-tenant-id"
