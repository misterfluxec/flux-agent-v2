from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class CountryProfile(BaseModel):
    country_code: str
    currency: str
    timezone: str
    identity_rules: Dict[str, str]  # e.g., {"id_name": "RUC", "pattern": "^[0-9]{13}$"}
    tax_system: str
    common_payment_methods: List[str]
    business_hours: str = "09:00-18:00"
    
    # Fortress Path v2.3 Extensions
    phone_format: str
    week_start_day: str = "monday"
    language_code: str = "es"
    holidays_service: str # Key for holiday provider/logic
    tax_adapter_id: str

# Registry of LATAM Country Profiles
COUNTRY_PROFILES: Dict[str, CountryProfile] = {
    "EC": CountryProfile(
        country_code="EC",
        currency="USD",
        timezone="America/Guayaquil",
        identity_rules={"id_name": "RUC/Cédula", "pattern": r"^[0-9]{10,13}$"},
        tax_system="SRI",
        common_payment_methods=["Transferencia", "Efectivo", "Tarjeta"],
        phone_format="+593XXXXXXXXX",
        holidays_service="ec_holidays",
        tax_adapter_id="sri_ecuador"
    ),
    "MX": CountryProfile(
        country_code="MX",
        currency="MXN",
        timezone="America/Mexico_City",
        identity_rules={"id_name": "RFC", "pattern": r"^[A-Z&Ñ]{3,4}[0-9]{2}(0[1-9]|1[012])(0[1-9]|[12][0-9]|3[01])[A-Z0-9]{3}$"},
        tax_system="SAT",
        common_payment_methods=["OXXO", "SPEI", "Tarjeta"],
        phone_format="+52XXXXXXXXXX",
        holidays_service="mx_holidays",
        tax_adapter_id="sat_mexico"
    ),
    "CO": CountryProfile(
        country_code="CO",
        currency="COP",
        timezone="America/Bogota",
        identity_rules={"id_name": "NIT/Cédula", "pattern": r"^[0-9]{8,10}$"},
        tax_system="DIAN",
        common_payment_methods=["PSE", "Efectivo", "Tarjeta"],
        phone_format="+57XXXXXXXXXX",
        holidays_service="co_holidays",
        tax_adapter_id="dian_colombia"
    ),
    "BR": CountryProfile(
        country_code="BR",
        currency="BRL",
        timezone="America/Sao_Paulo",
        identity_rules={"id_name": "CPF/CNPJ", "pattern": r"^[0-9]{11,14}$"},
        tax_system="Receita Federal",
        common_payment_methods=["Pix", "Boleto", "Tarjeta"],
        phone_format="+55XXXXXXXXXX",
        week_start_day="sunday",
        holidays_service="br_holidays",
        tax_adapter_id="rf_brazil"
    )
}

def get_country_profile(code: str) -> Optional[CountryProfile]:
    return COUNTRY_PROFILES.get(code.upper())
