# FluxAgent V2 - Infraestructura y Puertos

**IMPORTANTE: NUNCA USAR NI ASUMIR COOLIFY. ESTE PROYECTO ES TOTALMENTE INDEPENDIENTE.**

## Mapeo de Puertos y Dominios Cloudflare

Este proyecto está configurado para salir a través de Cloudflare Tunnels (o proxy) utilizando los siguientes puertos locales en el servidor:

| Servicio | Dominio Público | Puerto Local | Descripción |
| :--- | :--- | :--- | :--- |
| **Frontend (React/Next.js)** | `app.labodegaec.com` | `4000` (o `3000`) | Interfaz de usuario web. El servidor dev corre en 3000/4000. |
| **Backend (FastAPI)** | `api.labodegaec.com` | `9000` | API principal, lógica del agente y endpoints. |
| **Evolution API / WhatsApp** | `wa.labodegaec.com` | `8081` | Microservicio para conexiones de WhatsApp. |

## Reglas Críticas
1. **NO MENCIONAR NI USAR COOLIFY:** Cualquier mención a Coolify corresponde a otros proyectos del servidor que ocupan el puerto 8000.
2. **Backend API:** Las peticiones `fetch` o `curl` locales hacia el backend deben usar el puerto **9000**.
3. **Independencia:** Si algún contenedor o variable de entorno se configuró asumiendo integraciones externas (como Coolify), deben desvincularse. FluxAgent debe funcionar como un ecosistema aislado (`flux-agent-v2`).
