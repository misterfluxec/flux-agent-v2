"""
seed_nail_spa_v2.py — Seed con endpoints reales del backend
============================================================
Endpoints confirmados:
  /api/v1/agents           POST — crear agente
  /api/v1/catalog/import   POST — importar catálogo masivo
  /api/v1/catalog/{id}     PATCH — actualizar item
  /api/v1/leads            GET — leads/clientes
  /api/v1/commerce/orders  GET — órdenes
  /api/v1/commerce/quotes  GET — cotizaciones
  /api/v1/ingest/start     POST — ingestar conocimiento
"""

import requests, json, time
from datetime import datetime, timedelta, timezone

BASE = "http://localhost:9000/api/v1"
EMAIL = "maritza@mendoza.com"
PASSWORD = "Mendoza2026!"

def login():
    r = requests.post(f"{BASE}/auth/login",
        json={"email": EMAIL, "password": PASSWORD}, timeout=10)
    d = r.json()
    token = d["access_token"]
    tenant_id = d["usuario"]["tenant_id"]
    print(f"✅ Login OK | Tenant: {tenant_id} | Plan: {d['usuario']['plan']}")
    return token, tenant_id

def H(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def api(method, url, token, data=None, params=None):
    fn = getattr(requests, method)
    kw = {"headers": H(token), "timeout": 15}
    if data: kw["json"] = data
    if params: kw["params"] = params
    r = fn(f"{BASE}{url}", **kw)
    if r.status_code not in (200, 201):
        print(f"  ⚠️  {method.upper()} {url} → {r.status_code}: {r.text[:100]}")
        return None
    return r.json()

# ────────────────────────────────────────────────────────────────────────────
def step1_create_agent(token):
    print("\n🤖 Paso 1: Creando Agente Luna...")
    r = api("post", "/agents", token, {
        "nombre": "Luna — Nail Spa Mendoza",
        "area": "ventas",
        "descripcion": "Agente especializada en agendamiento de citas y ventas de servicios del Nail Spa Mendoza",
        "genero": "femenino",
        "personalidad": "Amigable, profesional y entusiasta. Conoce perfectamente todos los servicios del spa.",
        "idioma": "español",
        "tono": "cálido y profesional",
        "canales": ["whatsapp", "web_chat"],
        "tipo_negocio": "Spa de uñas y manicure profesional",
        "objetivo": "Agendar citas, responder consultas sobre precios, promover ofertas vigentes y dar seguimiento post-servicio.",
        "instrucciones": (
            "Eres Luna, la asistente virtual del Nail Spa Mendoza. Tu misión:\n\n"
            "1. AGENDAMIENTO: Ayuda a las clientas a agendar, modificar o cancelar citas. "
            "Pregunta el servicio deseado, fecha y horario preferido.\n"
            "2. INFORMACIÓN: Responde precios y características de cada servicio del catálogo.\n"
            "3. PROMOCIONES: Informa sobre: Martes de Manicure 20% OFF (código MARTES20), "
            "Primera visita 15% descuento (código BIENVENIDA15), Combo Novia (código NOVIA2026).\n"
            "4. RECORDATORIOS: Envía recordatorio 24 horas antes de cada cita.\n"
            "5. VENTAS: Sugiere upgrades — si piden clásica, ofrece gel por $10 más que dura 3 semanas.\n"
            "6. SEGUIMIENTO: Después del servicio, pregunta satisfacción y agenda próxima cita.\n\n"
            "HORARIO: Lun-Sáb 9:00-19:00 / Dom 10:00-17:00\n"
            "DIRECCIÓN: Av. Principal 123, frente al parque central\n"
            "TELÉFONO: +593 99 123 4567\n\n"
            "Responde en español, tono cálido y profesional. Emojis con moderación 💅"
        ),
        "modelo": "qwen2.5:3b",
        "temperatura": 0.75,
        "max_tokens": 800,
        "agent_type": "sales",
        "specialty": "agendamiento y ventas de servicios de belleza",
        "system_prompt": (
            "Eres Luna, asistente virtual del Nail Spa Mendoza. "
            "Especializada en agendamiento de citas y ventas de servicios de manicure y pedicure profesional. "
            "Siempre saluda con calidez y ofrece ayuda concreta."
        ),
        "script_ventas": {
            "saludo": "¡Hola! Soy Luna 💅 del Nail Spa Mendoza.",
            "introduccion": "¿Te gustaría agendar una cita o conocer nuestros servicios y promociones de esta semana?",
            "oferta": "Recuerda que tenemos Martes de Manicure con 20% de descuento."
        },
        "estado": "activo",
    })
    if r:
        aid = r.get("id") or r.get("agente", {}).get("id", "")
        print(f"  ✅ Agente creado: {aid}")
        return aid
    return None

# ────────────────────────────────────────────────────────────────────────────
def step2_import_catalog(token):
    print("\n📦 Paso 2: Importando catálogo de servicios y productos...")
    items = [
        # SERVICIOS
        {"sku": "SVC-MAN-001", "nombre": "Manicure Clásica",
         "descripcion": "Limpieza, forma y esmaltado tradicional",
         "precio": 12.0, "type": "service", "categoria": "manicure",
         "duracion_minutos": 45, "activo": True},
        {"sku": "SVC-MAN-002", "nombre": "Manicure Gel UV",
         "descripcion": "Esmaltado gel con lámpara UV, dura 3 semanas",
         "precio": 22.0, "type": "service", "categoria": "manicure",
         "duracion_minutos": 60, "activo": True},
        {"sku": "SVC-MAN-003", "nombre": "Manicure Acrílico",
         "descripcion": "Extensión acrílica completa con decoración",
         "precio": 35.0, "type": "service", "categoria": "manicure",
         "duracion_minutos": 90, "activo": True},
        {"sku": "SVC-MAN-004", "nombre": "Manicure Semipermanente",
         "descripcion": "Semipermanente de alta duración 2-3 semanas",
         "precio": 18.0, "type": "service", "categoria": "manicure",
         "duracion_minutos": 55, "activo": True},
        {"sku": "SVC-PED-001", "nombre": "Pedicure Clásica",
         "descripcion": "Baño, exfoliación, corte y esmaltado",
         "precio": 15.0, "type": "service", "categoria": "pedicure",
         "duracion_minutos": 50, "activo": True},
        {"sku": "SVC-PED-002", "nombre": "Pedicure Spa Completo",
         "descripcion": "Spa con sales, mascarilla y masaje de pies",
         "precio": 28.0, "type": "service", "categoria": "pedicure",
         "duracion_minutos": 75, "activo": True},
        {"sku": "SVC-PED-003", "nombre": "Pedicure Gel UV",
         "descripcion": "Pedicure con gel UV de larga duración",
         "precio": 25.0, "type": "service", "categoria": "pedicure",
         "duracion_minutos": 65, "activo": True},
        {"sku": "SVC-ART-001", "nombre": "Nail Art por Uña",
         "descripcion": "Decoración artística personalizada por uña",
         "precio": 3.0, "type": "service", "categoria": "nail_art",
         "duracion_minutos": 15, "activo": True},
        {"sku": "SVC-ART-002", "nombre": "Nail Art Premium",
         "descripcion": "Diseños complejos con pedrería y efectos 3D",
         "precio": 8.0, "type": "service", "categoria": "nail_art",
         "duracion_minutos": 30, "activo": True},
        {"sku": "SVC-RET-001", "nombre": "Retiro de Acrílico",
         "descripcion": "Retiro seguro sin dañar la uña natural",
         "precio": 10.0, "type": "service", "categoria": "retiro",
         "duracion_minutos": 30, "activo": True},
        {"sku": "SVC-RET-002", "nombre": "Retiro de Gel",
         "descripcion": "Retiro de esmalte gel con acetona especial",
         "precio": 8.0, "type": "service", "categoria": "retiro",
         "duracion_minutos": 20, "activo": True},
        {"sku": "SVC-CMB-001", "nombre": "Combo Mani + Pedi Clásico",
         "descripcion": "Manicure y pedicure clásicos juntos — ahorra $3",
         "precio": 24.0, "type": "service", "categoria": "combo",
         "duracion_minutos": 90, "activo": True},
        {"sku": "SVC-CMB-002", "nombre": "Combo Mani Gel + Pedi Spa",
         "descripcion": "Manicure gel y pedicure spa completo — ahorra $5",
         "precio": 45.0, "type": "service", "categoria": "combo",
         "duracion_minutos": 120, "activo": True},
        # PRODUCTOS
        {"sku": "PRD-GEL-001", "nombre": "Esmalte Gel OPI Rojo Pasión",
         "descripcion": "Esmalte gel profesional color rojo intenso 15ml",
         "precio": 8.50, "precio_costo": 3.50, "type": "physical",
         "categoria": "esmaltes", "stock": 24, "activo": True},
        {"sku": "PRD-GEL-002", "nombre": "Esmalte Gel OPI Rosa Nude",
         "descripcion": "Gel tono nude ideal para uso diario 15ml",
         "precio": 8.50, "precio_costo": 3.50, "type": "physical",
         "categoria": "esmaltes", "stock": 18, "activo": True},
        {"sku": "PRD-GEL-003", "nombre": "Esmalte Gel OPI French White",
         "descripcion": "Blanco puro para uñas francesa 15ml",
         "precio": 8.50, "precio_costo": 3.50, "type": "physical",
         "categoria": "esmaltes", "stock": 30, "activo": True},
        {"sku": "PRD-ACR-001", "nombre": "Kit Acrílico Profesional",
         "descripcion": "Polvo y líquido para extensiones acrílicas 100g+60ml",
         "precio": 45.0, "precio_costo": 18.0, "type": "physical",
         "categoria": "acrilico", "stock": 8, "activo": True},
        {"sku": "PRD-HRR-001", "nombre": "Lima Eléctrica Manicure 20K RPM",
         "descripcion": "Torno eléctrico profesional con 6 cabezales",
         "precio": 120.0, "precio_costo": 55.0, "type": "physical",
         "categoria": "herramientas", "stock": 3, "activo": True},
        {"sku": "PRD-CRM-001", "nombre": "Crema Hidratante Manos SPA",
         "descripcion": "Crema nutritiva con aloe vera y vitamina E 250ml",
         "precio": 12.0, "precio_costo": 4.50, "type": "physical",
         "categoria": "cuidado", "stock": 45, "activo": True},
        {"sku": "PRD-SAL-001", "nombre": "Sales de Baño Lavanda",
         "descripcion": "Sales aromáticas para pedicure spa 500g",
         "precio": 6.50, "precio_costo": 2.0, "type": "physical",
         "categoria": "pedicure", "stock": 60, "activo": True},
        {"sku": "PRD-TOP-001", "nombre": "Top Coat Brillante UV",
         "descripcion": "Sellador de alto brillo para gel 10ml",
         "precio": 7.0, "precio_costo": 2.50, "type": "physical",
         "categoria": "esmaltes", "stock": 20, "activo": True},
    ]
    r = api("post", "/catalog/import", token, {"items": items})
    if r:
        n = r.get("total_importados") or r.get("imported") or len(items)
        print(f"  ✅ Catálogo importado: {n} ítems")
    return r

# ────────────────────────────────────────────────────────────────────────────
def step3_ingest_knowledge(token):
    print("\n🧠 Paso 3: Ingiriendo conocimiento del negocio...")
    knowledge = {
        "fuente": "manual",
        "nombre": "Spa Mendoza — Base de Conocimiento",
        "contenido": """
# Nail Spa Mendoza — Información Completa del Negocio

## Datos Generales
- **Nombre**: Nail Spa Mendoza
- **Propietaria**: Maritza Mendoza
- **Dirección**: Av. Principal 123, frente al parque central
- **Teléfono**: +593 99 123 4567
- **Email**: maritza@mendoza.com
- **Horario**: Lunes a Sábado 9:00 AM - 7:00 PM | Domingos 10:00 AM - 5:00 PM

## Catálogo de Servicios

### Manicure
| Servicio | Precio | Duración |
|---------|--------|----------|
| Manicure Clásica | $12 | 45 min |
| Manicure Semipermanente | $18 | 55 min |
| Manicure Gel UV (dura 3 semanas) | $22 | 60 min |
| Manicure Acrílico (extensiones) | $35 | 90 min |

### Pedicure
| Servicio | Precio | Duración |
|---------|--------|----------|
| Pedicure Clásica | $15 | 50 min |
| Pedicure Gel UV | $25 | 65 min |
| Pedicure Spa Completo (con masaje) | $28 | 75 min |

### Nail Art
| Servicio | Precio | Duración |
|---------|--------|----------|
| Nail Art por uña | $3/uña | 15 min |
| Nail Art Premium (pedrería, 3D) | $8/uña | 30 min |

### Retiros
| Servicio | Precio | Duración |
|---------|--------|----------|
| Retiro de Gel | $8 | 20 min |
| Retiro de Acrílico | $10 | 30 min |

### Combos (Más Populares)
| Combo | Precio | Ahorro |
|-------|--------|--------|
| Combo Mani + Pedi Clásico | $24 | $3 |
| Combo Mani Gel + Pedi Spa | $45 | $5 |

## Promociones Vigentes
1. **MARTES20**: 20% de descuento en todos los servicios de manicure los martes
2. **BIENVENIDA15**: 15% de descuento para clientes nuevas en su primera visita
3. **NOVIA2026**: Combo especial para novias — Mani Gel + Pedi Spa + Nail Art por $55 (ahorra $15)

## Políticas
- **Reservas**: Se puede agendar por WhatsApp, llamada o en persona
- **Cancelaciones**: Con 2 horas de anticipación sin cargo. Tardanza mayor a 15 min = cita cancelada
- **Pago**: Efectivo, transferencia bancaria o tarjeta (sin recargo)
- **Garantía**: Si el esmalte gel se daña en los primeros 5 días, retoque sin costo

## Preguntas Frecuentes
**¿Cuánto dura el gel?** — El gel UV dura entre 2 y 3 semanas según el cuidado.
**¿El acrílico daña las uñas?** — Con aplicación y retiro profesional, no daña las uñas naturales.
**¿Puedo venir con niñas?** — Sí, ofrecemos manicure clásica para niñas a $8.
**¿Tienen estacionamiento?** — Sí, hay parking disponible en la planta baja del edificio.
""",
        "metadata": {
            "negocio": "nail_spa",
            "version": "1.0",
            "idioma": "es",
        }
    }
    r = api("post", "/ingest/start", token, knowledge)
    if r:
        print(f"  ✅ Conocimiento ingirido — job_id: {r.get('job_id', 'ok')}")
    return r

# ────────────────────────────────────────────────────────────────────────────
def step4_verify(token):
    print("\n🔍 Paso 4: Verificando estado final...")

    # Check catalog
    catalog = api("get", "/catalog", token)
    if catalog:
        items = catalog if isinstance(catalog, list) else catalog.get("items", catalog.get("data", []))
        print(f"  📦 Catálogo: {len(items)} ítems")

    # Check agents
    agents = api("get", "/agents", token)
    if agents:
        ag_list = agents if isinstance(agents, list) else agents.get("agentes", agents.get("data", []))
        print(f"  🤖 Agentes: {len(ag_list)}")
        for ag in ag_list:
            print(f"     → {ag.get('nombre', ag.get('name', '?'))} | estado: {ag.get('estado', '?')}")

    # Check analytics
    kpis = api("get", "/analytics/kpis", token)
    if kpis:
        print(f"  📊 Analytics KPIs: disponibles")

    # Check leads
    leads = api("get", "/leads", token)
    if leads:
        leads_list = leads if isinstance(leads, list) else leads.get("data", leads.get("leads", []))
        print(f"  👥 Leads/Clientes: {len(leads_list)}")

    # Test agent chat
    print("\n💬 Probando chat con Luna...")
    chat_r = api("post", "/chat", token, {
        "mensaje": "Hola, quiero agendar una manicure gel para el martes",
        "canal": "web_chat",
        "contact_id": "test-client-001",
    })
    if chat_r:
        resp = chat_r.get("respuesta") or chat_r.get("response") or chat_r.get("message", "")
        print(f"  🤖 Luna responde: {resp[:150]}...")


def main():
    print("\n" + "="*65)
    print("💅 SEED NAIL SPA MENDOZA — FluxAgent V2")
    print("="*65)

    token, tenant_id = login()

    agent_id = step1_create_agent(token)
    step2_import_catalog(token)
    step3_ingest_knowledge(token)

    time.sleep(2)  # let background jobs settle
    step4_verify(token)

    print("\n" + "="*65)
    print("🎉 SEED COMPLETADO")
    print("="*65)
    print(f"  🔑 Email:     maritza@mendoza.com")
    print(f"  🔑 Password:  Mendoza2026!")
    print(f"  🌐 Dashboard: http://localhost:3000")
    print(f"  🤖 Agente:    Luna (agendamiento + ventas spa)")
    print(f"  📦 Catálogo:  13 servicios + 8 productos")
    print(f"  🧠 Knowledge: Base completa del negocio ingirida")
    print("="*65)


if __name__ == "__main__":
    main()
