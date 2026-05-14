import os
import glob

def generate_audit_export():
    project_root = "/home/mister/flux-agent-v2"
    src_root = os.path.join(project_root, "src")
    export_file = "/home/mister/.gemini/antigravity/brain/86c06bf2-14bb-42e8-a162-4c1884a3a0d9/backend-audit-export.md"
    
    with open(export_file, "w") as f:
        f.write("# Backend Audit Export - FluxAgent OS\n\n")
        
        # 1. Directory Tree
        f.write("## 1. Directory Tree (/src)\n")
        f.write("```\n")
        # Use find for the tree
        tree = os.popen(f"find {src_root} -maxdepth 4 -not -path '*/.*'").read()
        f.write(tree)
        f.write("```\n\n")
        
        # 2. File Contents
        f.write("## 2. Source Code (/src)\n\n")
        for root, dirs, files in os.walk(src_root):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, project_root)
                    f.write(f"### {rel_path}\n")
                    f.write(f"**Path**: `{full_path}`\n\n")
                    f.write("```python\n")
                    try:
                        with open(full_path, "r") as py_file:
                            f.write(py_file.read())
                    except Exception as e:
                        f.write(f"# Error reading file: {e}")
                    f.write("\n```\n\n")
                    f.write("---\n\n")
        
        # 3. Docker Compose
        f.write("## 3. Docker Configuration\n\n")
        docker_compose = os.path.join(project_root, "docker-compose.yml")
        if os.path.exists(docker_compose):
            f.write("### docker-compose.yml\n")
            f.write("```yaml\n")
            with open(docker_compose, "r") as dc_file:
                f.write(dc_file.read())
            f.write("\n```\n\n")
            
        # 4. SQL Migrations
        f.write("## 4. SQL Migrations\n\n")
        migration_dirs = [
            os.path.join(project_root, "init-db"),
            os.path.join(project_root, "migrations")
        ]
        
        all_migrations = []
        for d in migration_dirs:
            if os.path.exists(d):
                all_migrations.extend(glob.glob(os.path.join(d, "*.sql")))
        
        # Sort by filename
        all_migrations.sort(key=lambda x: os.path.basename(x))
        
        for m in all_migrations:
            rel_m = os.path.relpath(m, project_root)
            f.write(f"### {rel_m}\n")
            f.write("```sql\n")
            with open(m, "r") as sql_file:
                f.write(sql_file.read())
            f.write("\n```\n\n")
            
        # 5. Requirements
        f.write("## 5. Dependencies\n\n")
        reqs = os.path.join(project_root, "requirements.txt")
        if os.path.exists(reqs):
            f.write("### requirements.txt\n")
            f.write("```\n")
            with open(reqs, "r") as req_file:
                f.write(req_file.read())
            f.write("\n```\n\n")
            
        # 6. Environment Variables
        f.write("## 6. Environment Variables (.env.example)\n\n")
        env_ex = os.path.join(project_root, ".env.example")
        if os.path.exists(env_ex):
            f.write("```\n")
            with open(env_ex, "r") as env_file:
                for line in env_file:
                    if "=" in line and not line.strip().startswith("#"):
                        key = line.split("=")[0]
                        f.write(f"{key}=\n")
                    else:
                        f.write(line)
            f.write("\n```\n")

if __name__ == "__main__":
    generate_audit_export()
