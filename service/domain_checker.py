"""
Verificador de integridade e regras de domínio da pasta service/.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, List, Tuple


ALLOWED_ROOT_FILES = {"__init__.py", "README.md", "RULES.md", "domain_checker.py"}


def check_service_domains(service_dir: Path) -> Tuple[bool, List[str], Dict[str, List[str]]]:
    """
    Verifica se a pasta service/ respeita as regras de delimitação de domínio:
    1. Não permite arquivos de lógica soltos na raiz de service/.
    2. Exige que todo código pertença a uma subpasta de domínio.
    3. Exige que cada subpasta de domínio contenha um __init__.py.
    """
    violations: List[str] = []
    domains: Dict[str, List[str]] = {}
    is_valid = True

    if not service_dir.exists():
        return False, [f"Diretório '{service_dir}' não existe."], {}

    # 1. Checa arquivos na raiz de service/
    for item in service_dir.iterdir():
        if item.is_file():
            if item.name not in ALLOWED_ROOT_FILES:
                violations.append(
                    f"Violação de Domínio: Arquivo '{item.name}' encontrado solto na raiz de service/. "
                    f"Ele deve pertencer a uma subpasta de domínio (Bounded Context)."
                )
                is_valid = False
        elif item.is_dir() and not item.name.startswith((".", "__")):
            domain_name = item.name
            init_file = item / "__init__.py"
            if not init_file.exists():
                violations.append(
                    f"Violação de Pacote: Subpasta de domínio '{domain_name}' não possui '__init__.py'."
                )
                is_valid = False

            # Registra arquivos pertencentes ao domínio (ignorando __pycache__)
            domain_files = [
                f.name for f in item.glob("**/*")
                if f.is_file() and "__pycache__" not in f.parts
            ]
            domains[domain_name] = domain_files

    return is_valid, violations, domains


def detect_git_changes_in_service(repo_root: Path) -> List[str]:
    """Detecta arquivos modificados ou adicionados em service/ via git status."""
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain", "service/"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=True
        )
        changed_files = []
        for line in res.stdout.strip().split("\n"):
            if line:
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    changed_files.append(parts[1])
        return changed_files
    except Exception:
        return []
