from typing import Dict, Any

BUSINESS_PROFILES: Dict[str, Dict[str, Any]] = {
    "retail": {
        "name": "Retail & E-commerce",
        "default_agent_type": "sales",
        "default_agent_name": "Yanua Ventas",
        "catalog_seed": [
            {
                "name": "Producto Estrella (Ejemplo)",
                "type": "physical_product",
                "base_price": 50.00,
                "stock_quantity": 100,
                "sales_playbook": {
                    "positioning": "El producto más vendido, ideal para regalos.",
                    "ideal_customer": ["Comprador impulsivo", "Buscador de regalos"],
                    "objection_handling": {
                        "price": "Destacar que la calidad justifica el price y dura 3 veces más que la competencia.",
                        "tiempo_envio": "Ofrecer envío express (upsell)."
                    },
                    "urgency_triggers": ["Solo quedan pocas unidades en este color."]
                },
                "commercial_strategy": {
                    "upsells": ["Envío Express", "Garantía Extendida"],
                    "fallback_offer": "Versión básica (si el price es problema)"
                }
            },
            {
                "name": "Envío Express",
                "type": "service",
                "base_price": 10.00,
                "sales_playbook": {
                    "positioning": "La forma más rápida de recibir tu producto."
                }
            }
        ],
        "workflows": ["cart_recovery", "low_stock_alert", "post_purchase_survey"]
    },
    "clinic": {
        "name": "Salud & Bienestar",
        "default_agent_type": "reception",
        "default_agent_name": "Yanua Recepción",
        "catalog_seed": [
            {
                "name": "Consulta General",
                "type": "appointment",
                "base_price": 45.00,
                "sales_playbook": {
                    "positioning": "Revisión completa con especialistas certificados.",
                    "objection_handling": {
                        "disponibilidad": "Ofrecer entrar en lista de espera prioritaria o el siguiente turno disponible.",
                        "price": "Recordar que aceptamos aseguradoras (pedir name del seguro)."
                    },
                    "closing_style": "consultative"
                }
            },
            {
                "name": "Revisión Rápida",
                "type": "appointment",
                "base_price": 20.00,
                "sales_playbook": {
                    "positioning": "Para chequeos de rutina y lectura de exámenes."
                }
            }
        ],
        "resources_seed": [
            {"name": "Consultorio 1", "type": "room", "capacity": 1},
            {"name": "Dr. Pérez", "type": "human"},
        ],
        "workflows": ["appointment_reminder_24h", "patient_feedback", "no_show_followup"]
    },
    "services": {
        "name": "Servicios Profesionales",
        "default_agent_type": "support",
        "default_agent_name": "Yanua Soporte",
        "catalog_seed": [
            {
                "name": "Asesoría Inicial (Discovery)",
                "type": "service",
                "base_price": 0.00,
                "sales_playbook": {
                    "positioning": "Reunión de diagnóstico gratuita para entender el problema.",
                    "closing_style": "direct",
                    "urgency_triggers": ["Agenda limitada esta semana."]
                }
            },
            {
                "name": "Proyecto Completo",
                "type": "custom_offer",
                "base_price": 1000.00,
                "sales_playbook": {
                    "positioning": "Solución end-to-end personalizada.",
                    "objection_handling": {
                        "presupuesto": "Ofrecer pago en hitos (3 cuotas)."
                    }
                }
            }
        ],
        "workflows": ["quote_followup_48h", "project_status_update", "invoice_reminder"]
    }
}
