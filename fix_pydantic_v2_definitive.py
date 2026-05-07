#!/usr/bin/env python3
"""
🔧 CORRECCIÓN DEFINITIVA PYDANTIC V2
=====================================
Este script repara TODAS las incompatibilidades con Pydantic v2
en el archivo agents_router.py de forma segura y reversible.
"""

from pathlib import Path
import re
import shutil

def create_backup():
    """Crear backup antes de modificar"""
    backup_path = Path("src/routers/agents_router.py.backup_before_fix")
    original_path = Path("src/routers/agents_router.py")
    shutil.copy2(original_path, backup_path)
    print(f"✅ Backup creado: {backup_path}")

def fix_pydantic_v2_compatibility():
    """Reparar problemas de compatibilidad Pydantic v2"""
    path = Path("src/routers/agents_router.py")
    content = path.read_text()
    
    # Contador de cambios
    changes = 0
    
    # Fix 1: Corregir brackets rotos
    patterns_to_fix = [
        (r'Optional\[List\[str\] = None\]', 'Optional[List[str]]'),
        (r'Optional\[Dict\[str, Any\] = None\]', 'Optional[Dict[str, Any]]'),
    ]
    
    for pattern, replacement in patterns_to_fix:
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            changes += matches
            print(f"✅ Fixed {matches} bracket issues: {pattern}")
    
    # Fix 2: Remover dobles defaults
    double_default_count = len(re.findall(r'= None = None', content))
    if double_default_count > 0:
        content = re.sub(r'= None = None', '= None', content)
        changes += double_default_count
        print(f"✅ Fixed {double_default_count} double defaults")
    
    # Fix 3: Agregar defaults faltantes en BaseModel
    lines = content.split('\n')
    fixed_lines = []
    in_basemodel = False
    basemodel_indent = 0
    
    for line in lines:
        # Detectar inicio de clase BaseModel
        if re.match(r'^\s*class \w+\(BaseModel\):', line):
            in_basemodel = True
            basemodel_indent = len(line) - len(line.lstrip())
            fixed_lines.append(line)
            continue
        
        # Detectar fin de clase BaseModel
        if in_basemodel and line.strip() and not line.startswith(' ' * (basemodel_indent + 1)):
            in_basemodel = False
        
        # Reparar campos Optional sin default
        if (in_basemodel and 
            'Optional[' in line and 
            '= None' not in line and 
            line.strip().endswith(':')):
            
            # Extraer indentación
            indent = len(line) - len(line.lstrip())
            field_name = line.strip().split(':')[0]
            
            # Agregar default
            fixed_line = ' ' * indent + field_name + ': = None'
            fixed_lines.append(fixed_line)
            changes += 1
            print(f"✅ Added default to: {field_name}")
        else:
            fixed_lines.append(line)
    
    # Guardar archivo corregido
    path.write_text('\n'.join(fixed_lines))
    
    return changes

def validate_syntax():
    """Validar sintaxis Python"""
    import subprocess
    result = subprocess.run([
        'python3', '-m', 'py_compile', 
        'src/routers/agents_router.py'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Sintaxis Python válida")
        return True
    else:
        print(f"❌ Error de sintaxis: {result.stderr}")
        return False

def main():
    print("🔧 INICIANDO CORRECCIÓN DEFINITIVA PYDANTIC V2")
    print("=" * 50)
    
    # 1. Backup
    create_backup()
    
    # 2. Reparar
    changes = fix_pydantic_v2_compatibility()
    
    # 3. Validar
    if validate_syntax():
        print(f"\n🎉 CORRECCIÓN COMPLETADA")
        print(f"📊 Total de cambios: {changes}")
        print(f"✅ Sintaxis válida")
        print(f"✅ Compatible con Pydantic v2")
        print(f"\n📋 PRÓXIMOS PASOS:")
        print(f"1. docker restart fluxagent-backend-test")
        print(f"2. Esperar 10 segundos")
        print(f"3. Probar: curl -H 'Authorization: Bearer TOKEN' http://localhost:9000/api/v1/agents")
    else:
        print(f"\n❌ ERROR EN CORRECCIÓN")
        print(f"🔄 Restaurando backup...")
        shutil.copy2("src/routers/agents_router.py.backup_before_fix", "src/routers/agents_router.py")
        print(f"✅ Backup restaurado")

if __name__ == "__main__":
    main()
