import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# Configuramos Jinja2
template_dir = os.path.join(os.path.dirname(__file__), "../../../templates/pdf")
env = Environment(loader=FileSystemLoader(template_dir))

async def generate_quote_pdf(quote: dict, tenant_name: str, items: list, tenant_config: dict = None) -> bytes:
    """
    Genera PDF profesional de cotización usando HTML + Jinja2 + WeasyPrint
    """
    if tenant_config is None:
        tenant_config = {}
        
    # Seleccionar theme
    theme_name = tenant_config.get("pdf_theme", "quote_default.html")
    template = env.get_template(theme_name)
    
    # Renderizar HTML
    html_out = template.render(
        quote=quote,
        items=items,
        tenant_name=tenant_name,
        date=datetime.utcnow().strftime('%d/%m/%Y'),
        theme_color=tenant_config.get("brand_color", "#2563eb"),
        logo_url=tenant_config.get("logo_url"),
        legal_text=tenant_config.get("legal_text"),
        customer_name=quote.get("customer_name"),
        customer_email=quote.get("customer_email"),
        customer_phone=quote.get("customer_phone")
    )
    
    # Importar WeasyPrint de forma perezosa para no romper si no está instalado
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html_out).write_pdf()
        return pdf_bytes
    except ImportError:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("WeasyPrint no está instalado. Retornando HTML renderizado en su lugar.")
        return html_out.encode('utf-8')
