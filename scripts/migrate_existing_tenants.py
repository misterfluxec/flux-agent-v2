# scripts/migrate_existing_tenants.py
import os
import asyncio
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv(".env.production")
# Fallback a .env local si no existe el de producción
if not os.getenv("DATABASE_URL"):
    load_dotenv(".env")

DB_URL = os.getenv("DATABASE_URL", "postgresql://fluxadmin:fluxsecure2026@localhost:5434/fluxagent_v2")
engine = create_engine(DB_URL)

def migrate_tenants(dry_run: bool = True, target_plan: str = "growth"):
    """Asigna playbooks, inicializa cuotas y configura capacidades para beta"""
    with engine.begin() as conn:
        # 1. Obtener tenants sin playbook asignado
        tenants = conn.execute(text("""
            SELECT t.id, t.industry, t.name, t.email 
            FROM tenants t
            LEFT JOIN agents a ON t.id = a.tenant_id
            WHERE a.playbook_id IS NULL AND t.status = 'active'
        """)).fetchall()
        
        print(f"🔍 Found {len(tenants)} tenants to migrate. Dry run: {dry_run}")
        
        for t in tenants:
            tenant_id, industry, name, email = t
            
            if dry_run:
                print(f"  📝 [DRY] Assigning {industry} playbook to {name} ({tenant_id})")
                continue
            
            # 2. Crear/Asignar CommercialPlaybook
            playbook_id = conn.execute(text("""
                INSERT INTO commercial_playbooks (tenant_id, industry, name, personality, workflows, objection_rules, sla_rules, kpi_targets, is_system_template)
                SELECT :tenant_id, :industry, :name, 
                       '{"tone":"adaptado","focus":"operacional"}'::jsonb,
                       '[]'::jsonb, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, false
                ON CONFLICT (tenant_id, industry, version) DO UPDATE SET updated_at = NOW()
                RETURNING id
            """), {"tenant_id": tenant_id, "industry": industry or "services", "name": f"{industry.capitalize()} Playbook"}).scalar()
            
            # 3. Asignar a agente principal
            conn.execute(text("""
                UPDATE agents SET playbook_id = :pid WHERE tenant_id = :tid AND is_default = true
            """), {"pid": playbook_id, "tid": tenant_id})
            
            # 4. Inicializar MonthlyQuota
            conn.execute(text("""
                INSERT INTO monthly_quotas (tenant_id, period, can_use_realtime_ops, can_export_pdf, can_use_advanced_analytics)
                VALUES (:tid, TO_CHAR(NOW(), 'YYYY-MM'), true, true, true)
                ON CONFLICT (tenant_id, period) DO NOTHING
            """), {"tid": tenant_id})
            
            print(f"  ✅ Migrated: {name} → {industry} playbook")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Simular migración sin escribir")
    parser.add_argument("--plan", default="growth", help="Plan por defecto para beta testers")
    args = parser.parse_args()
    
    migrate_tenants(dry_run=args.dry_run, target_plan=args.plan)
    print("🏁 Migration complete." if not args.dry_run else "🔍 Dry run finished.")
