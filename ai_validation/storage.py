"""
Gerenciador de armazenamento de prompts e relatórios em subpastas individuais.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .validator import ValidationReport


class PromptStorage:
    """Responsável por persistir cada prompt e seu relatório de validação em uma subpasta dedicada."""

    DEFAULT_BASE_DIR = Path(__file__).parent / "prompts"

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = (base_dir or self.DEFAULT_BASE_DIR).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _slugify(text: str, max_length: int = 30) -> str:
        """Gera um slug amigável a partir do texto do prompt."""
        # Pega a primeira linha ou primeiras palavras
        first_line = text.strip().split("\n")[0]
        cleaned = re.sub(r"[^\w\s-]", "", first_line).strip().lower()
        slug = re.sub(r"[-\s]+", "_", cleaned)
        return slug[:max_length].strip("_") or "prompt"

    def save_prompt(
        self,
        prompt_text: str,
        report: ValidationReport,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        response_text: Optional[str] = None,
        author: Optional[str] = None,
    ) -> Path:
        """
        Cria uma subpasta única e salva o prompt, relatório e metadados.

        Retorna o Path da subpasta criada.
        """
        now = datetime.now()
        timestamp_str = now.strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        slug = self._slugify(title or prompt_text)
        subfolder_name = f"{timestamp_str}_{slug}_{unique_id}"

        subfolder_path = self.base_dir / subfolder_name
        subfolder_path.mkdir(parents=True, exist_ok=True)

        # 1. Salvar o prompt original em Markdown
        prompt_file = subfolder_path / "prompt.md"
        prompt_content = (
            f"# Prompt: {title or slug.replace('_', ' ').title()}\n\n"
            f"- **Data/Hora:** {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"- **Status de Validação:** {report.status.value} (Score: {report.score}/100)\n\n"
            f"---\n\n"
            f"## Conteúdo Enviado\n\n"
            f"{prompt_text.strip()}\n"
        )
        prompt_file.write_text(prompt_content, encoding="utf-8")

        # 2. Salvar o relatório de validação detalhado
        report_file = subfolder_path / "validation_report.json"
        report_file.write_text(
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        # 3. Salvar metadados
        words = re.findall(r"\b[\w-]+\b", prompt_text)
        metadata = {
            "id": unique_id,
            "subfolder": subfolder_name,
            "created_at": now.isoformat(),
            "author": author or "system_user",
            "title": title or slug.replace("_", " ").title(),
            "tags": tags or [],
            "character_count": len(prompt_text),
            "word_count": len(words),
            "validation_status": report.status.value,
            "validation_score": report.score,
            "is_valid": report.is_valid,
            "files": {
                "prompt": "prompt.md",
                "validation_report": "validation_report.json",
                "response": "response.md" if response_text is not None else None,
            }
        }
        metadata_file = subfolder_path / "metadata.json"
        metadata_file.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        # 4. Salvar resposta (se fornecida)
        if response_text is not None:
            response_file = subfolder_path / "response.md"
            response_content = (
                f"# Resposta da IA\n\n"
                f"- **Gerada em:** {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"- **Prompt ID Vinculado:** {unique_id}\n\n"
                f"---\n\n"
                f"{response_text.strip()}\n"
            )
            response_file.write_text(response_content, encoding="utf-8")

        return subfolder_path

    def list_saved_prompts(self) -> List[Dict[str, Any]]:
        """Lista todas as subpastas de prompts salvas com resumo de seus metadados."""
        results = []
        if not self.base_dir.exists():
            return results

        # Itera em ordem cronológica reversa
        for subfolder in sorted(self.base_dir.iterdir(), reverse=True):
            if subfolder.is_dir() and not subfolder.name.startswith("."):
                meta_file = subfolder / "metadata.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            data["path"] = str(subfolder)
                            results.append(data)
                    except Exception:
                        continue
        return results

    def get_prompt_details(self, subfolder_name: str) -> Optional[Dict[str, Any]]:
        """Carrega os detalhes completos de um prompt salvo."""
        subfolder = self.base_dir / subfolder_name
        if not subfolder.is_dir():
            return None

        result: Dict[str, Any] = {"path": str(subfolder)}

        meta_file = subfolder / "metadata.json"
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                result["metadata"] = json.load(f)

        prompt_file = subfolder / "prompt.md"
        if prompt_file.exists():
            result["prompt_content"] = prompt_file.read_text(encoding="utf-8")

        report_file = subfolder / "validation_report.json"
        if report_file.exists():
            with open(report_file, "r", encoding="utf-8") as f:
                result["validation_report"] = json.load(f)

        response_file = subfolder / "response.md"
        if response_file.exists():
            result["response_content"] = response_file.read_text(encoding="utf-8")

        return result
