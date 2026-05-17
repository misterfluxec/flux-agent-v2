import re

def clean_for_whatsapp(text: str) -> str:
    """
    Limpia la respuesta del LLM para WhatsApp y TTS.
    Elimina markdown, normaliza símbolos y números.
    """
    # Eliminar markdown de formato
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*(.*?)\*', r'\1', text)        # *italic*
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'`(.*?)`', r'\1', text)          # `code`
    text = re.sub(r'#{1,6}\s', '', text)             # headers

    # Limpiar listas markdown
    text = re.sub(r'^\s*[-*+]\s+', '• ', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

    # Normalizar números y símbolos comunes
    text = text.replace('%', ' por ciento')
    text = text.replace('$', ' dólares ')
    text = text.replace('&', ' y ')
    text = text.replace('+', ' más ')

    # Limpiar espacios múltiples y líneas vacías extras
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'  +', ' ', text)
    text = text.strip()

    return text
