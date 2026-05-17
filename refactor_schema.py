import os
import re

# Directorios a escanear
DIRS_TO_SCAN = [
    "/home/mister/flux-agent-v2/src",
    "/home/mister/flux-agent-v2/frontend/src"
]

# Mapa de reemplazos (Spanish -> English)
REPLACEMENTS = {
    # Tenants
    r'\bnombre_empresa\b': 'company_name',
    r'\bemail_contacto\b': 'contact_email',
    r'\btelefono\b': 'phone',
    r'\bpais\b': 'country',
    r'\bzona_horaria\b': 'timezone',
    r'\bmax_agentes\b': 'max_agents',
    r'\bmax_mensajes_mes\b': 'max_messages_month',
    r'\bmensajes_usados_mes\b': 'messages_used_month',
    r'\bmax_instancias_whatsapp\b': 'max_whatsapp_instances',
    r'\bcontrato_inicio\b': 'contract_start',
    r'\bcontrato_fin\b': 'contract_end',
    r'\bcolor_primario\b': 'primary_color',
    r'\bdominio_personalizado\b': 'custom_domain',
    r'\bcreado_en\b': 'created_at',
    r'\bactualizado_en\b': 'updated_at',

    # Agents
    r'\bnombre\b': 'name',
    r'\bdescripcion\b': 'description',
    r'\bgenero\b': 'gender',
    r'\bhumor\b': 'mood',
    r'\bpersonalidad\b': 'personality',
    r'\bidioma\b': 'language',
    r'\btono\b': 'tone',
    r'\bcoleccion_rag\b': 'rag_collection',
    r'\btipo_negocio\b': 'business_type',
    r'\bobjetivo\b': 'objective',
    r'\binstrucciones\b': 'instructions',
    r'\bmodelo\b': 'model',
    r'\btemperatura\b': 'temperature',
    r'\bcanales\b': 'channels',
    r'\bhorario_inicio\b': 'schedule_start',
    r'\bhorario_fin\b': 'schedule_end',
    r'\bdias_atencion\b': 'service_days',
    r'\bmensaje_fuera_horario\b': 'off_hours_message',
    r'\bestado\b': 'status',
    r'\bscript_ventas\b': 'sales_script',

    # Usuarios
    r'\busuarios\b': 'users',
    r'\bultimo_login\b': 'last_login',
    r'\brol\b': 'role',

    # Plans
    r'\bprecio\b': 'price',
    r'\bmoneda\b': 'currency',
    r'\borden\b': 'sort_order',
    r'\bactivo\b': 'is_active',

    # Seguimientos -> follow_ups
    r'\bseguimientos\b': 'follow_ups',
    r'\bconversacion_id\b': 'conversation_id',
    r'\btipo\b': 'type',
    r'\bfecha_envio_programada\b': 'scheduled_send_at',
    r'\bmensaje_enviado\b': 'sent_message',
    r'\bintentos\b': 'attempts',

    # Tickets
    r'\basunto\b': 'subject',
    r'\bprioridad\b': 'priority'
}

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content
    for pattern, replacement in REPLACEMENTS.items():
        new_content = re.sub(pattern, replacement, new_content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    print("Iniciando refactorización de código...")
    files_modified = 0
    for directory in DIRS_TO_SCAN:
        for root, dirs, files in os.walk(directory):
            # Skip node_modules and .next
            if 'node_modules' in root or '.next' in root or '__pycache__' in root:
                continue
            for file in files:
                if file.endswith(('.py', '.ts', '.tsx', '.js', '.jsx')):
                    filepath = os.path.join(root, file)
                    try:
                        if process_file(filepath):
                            files_modified += 1
                            print(f"Modificado: {filepath}")
                    except Exception as e:
                        print(f"Error procesando {filepath}: {e}")
    
    print(f"\nTotal archivos modificados: {files_modified}")

    print("\nAplicando migraciones SQL en la base de datos...")
    sql_commands = """
    -- Tenants
    ALTER TABLE tenants RENAME COLUMN nombre_empresa TO company_name;
    ALTER TABLE tenants RENAME COLUMN email_contacto TO contact_email;
    ALTER TABLE tenants RENAME COLUMN telefono TO phone;
    ALTER TABLE tenants RENAME COLUMN pais TO country;
    ALTER TABLE tenants RENAME COLUMN zona_horaria TO timezone;
    ALTER TABLE tenants RENAME COLUMN estado TO status;
    ALTER TABLE tenants RENAME COLUMN creado_en TO created_at;
    ALTER TABLE tenants RENAME COLUMN actualizado_en TO updated_at;
    ALTER TABLE tenants RENAME COLUMN color_primario TO primary_color;
    ALTER TABLE tenants RENAME COLUMN dominio_personalizado TO custom_domain;
    ALTER TABLE tenants RENAME COLUMN max_agentes TO max_agents;
    ALTER TABLE tenants DROP COLUMN IF EXISTS max_mensajes_mes;
    ALTER TABLE tenants RENAME COLUMN mensajes_usados_mes TO messages_used_month;
    ALTER TABLE tenants RENAME COLUMN max_instancias_whatsapp TO max_whatsapp_instances;
    ALTER TABLE tenants RENAME COLUMN contrato_inicio TO contract_start;
    ALTER TABLE tenants RENAME COLUMN contrato_fin TO contract_end;

    -- Agents
    ALTER TABLE agents RENAME COLUMN nombre TO name;
    ALTER TABLE agents RENAME COLUMN descripcion TO description;
    ALTER TABLE agents RENAME COLUMN genero TO gender;
    ALTER TABLE agents RENAME COLUMN humor TO mood;
    ALTER TABLE agents RENAME COLUMN personalidad TO personality;
    ALTER TABLE agents RENAME COLUMN idioma TO language;
    ALTER TABLE agents RENAME COLUMN tono TO tone;
    ALTER TABLE agents RENAME COLUMN modelo TO model;
    ALTER TABLE agents RENAME COLUMN canales TO channels;
    ALTER TABLE agents RENAME COLUMN estado TO status;
    ALTER TABLE agents RENAME COLUMN creado_en TO created_at;
    ALTER TABLE agents RENAME COLUMN actualizado_en TO updated_at;
    ALTER TABLE agents RENAME COLUMN coleccion_rag TO rag_collection;
    ALTER TABLE agents RENAME COLUMN tipo_negocio TO business_type;
    ALTER TABLE agents RENAME COLUMN objetivo TO objective;
    ALTER TABLE agents RENAME COLUMN instrucciones TO instructions;
    ALTER TABLE agents RENAME COLUMN temperatura TO temperature;
    ALTER TABLE agents RENAME COLUMN horario_inicio TO schedule_start;
    ALTER TABLE agents RENAME COLUMN horario_fin TO schedule_end;
    ALTER TABLE agents RENAME COLUMN dias_atencion TO service_days;
    ALTER TABLE agents RENAME COLUMN mensaje_fuera_horario TO off_hours_message;
    ALTER TABLE agents RENAME COLUMN script_ventas TO sales_script;

    -- Usuarios -> users
    ALTER TABLE usuarios RENAME TO users;
    ALTER TABLE users RENAME COLUMN nombre TO name;
    ALTER TABLE users RENAME COLUMN estado TO status;
    ALTER TABLE users RENAME COLUMN idioma TO language;
    ALTER TABLE users RENAME COLUMN ultimo_login TO last_login;
    ALTER TABLE users RENAME COLUMN creado_en TO created_at;
    ALTER TABLE users RENAME COLUMN rol TO role;

    -- Plans
    ALTER TABLE plans RENAME COLUMN nombre TO name;
    ALTER TABLE plans RENAME COLUMN precio TO price;
    ALTER TABLE plans RENAME COLUMN moneda TO currency;
    ALTER TABLE plans RENAME COLUMN max_agentes TO max_agents;
    ALTER TABLE plans RENAME COLUMN max_instancias_whatsapp TO max_whatsapp_instances;
    ALTER TABLE plans RENAME COLUMN orden TO sort_order;
    ALTER TABLE plans RENAME COLUMN activo TO is_active;

    -- Seguimientos -> follow_ups
    ALTER TABLE seguimientos RENAME TO follow_ups;
    ALTER TABLE follow_ups RENAME COLUMN conversacion_id TO conversation_id;
    ALTER TABLE follow_ups RENAME COLUMN tipo TO type;
    ALTER TABLE follow_ups RENAME COLUMN estado TO status;
    ALTER TABLE follow_ups RENAME COLUMN fecha_envio_programada TO scheduled_send_at;
    ALTER TABLE follow_ups RENAME COLUMN mensaje_enviado TO sent_message;
    ALTER TABLE follow_ups RENAME COLUMN intentos TO attempts;
    ALTER TABLE follow_ups RENAME COLUMN creado_en TO created_at;
    ALTER TABLE follow_ups RENAME COLUMN actualizado_en TO updated_at;

    -- Tickets
    ALTER TABLE tickets RENAME COLUMN asunto TO subject;
    ALTER TABLE tickets RENAME COLUMN descripcion TO description;
    ALTER TABLE tickets RENAME COLUMN estado TO status;
    ALTER TABLE tickets RENAME COLUMN prioridad TO priority;
    ALTER TABLE tickets RENAME COLUMN creado_en TO created_at;
    ALTER TABLE tickets RENAME COLUMN actualizado_en TO updated_at;
    """
    
    with open('/tmp/migration.sql', 'w') as f:
        f.write(sql_commands)
        
    os.system("PGPASSWORD=fluxsecure2026 psql -h 172.21.0.2 -U fluxadmin -d fluxagent_v2 -f /tmp/migration.sql")
    print("Migración SQL finalizada.")

if __name__ == "__main__":
    main()
