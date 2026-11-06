"""
Testes unitários para o sistema de validação e persistência de prompts.
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from ai_validation.validator import PromptValidator, ValidationStatus
from ai_validation.storage import PromptStorage


class TestPromptValidator(unittest.TestCase):
    def setUp(self):
        self.validator = PromptValidator()

    def test_valid_architectural_prompt(self):
        prompt = (
            "Analise a arquitetura de microsserviços proposta em Python e Docker. "
            "Avalie os trade-offs de consistência eventual no banco de dados Postgres e Redis. "
            "Estruture a resposta em Markdown com diagrama Mermaid e não assuma "
            "nenhuma biblioteca externa sem justificar."
        )
        report = self.validator.validate(prompt)

        self.assertTrue(report.is_valid)
        self.assertIn(report.status, (ValidationStatus.APPROVED, ValidationStatus.WARNING))
        self.assertGreaterEqual(report.score, 70)
        self.assertEqual(len(report.violations), 0)

    def test_security_violation_openai_key(self):
        prompt = "Analise o código abaixo usando a chave sk-1234567890abcdef1234567890abcdef"
        report = self.validator.validate(prompt)

        self.assertFalse(report.is_valid)
        self.assertEqual(report.status, ValidationStatus.REJECTED)
        self.assertEqual(report.score, 0)
        self.assertTrue(any(v.rule_id == "SEC-01" for v in report.violations))

    def test_short_prompt_warning_or_rejection(self):
        prompt = "Olá IA"
        report = self.validator.validate(prompt)

        self.assertFalse(report.is_valid)
        self.assertEqual(report.status, ValidationStatus.REJECTED)
        self.assertTrue(any(v.rule_id == "LEN-01" for v in report.violations))


class TestPromptStorage(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.storage = PromptStorage(base_dir=self.temp_dir)
        self.validator = PromptValidator()

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_save_prompt_creates_subfolder_with_expected_files(self):
        prompt_text = (
            "Projete a arquitetura de mensageria usando Kafka e Python. "
            "Formate a resposta em Markdown e tabela comparativa. Não use componentes legados."
        )
        report = self.validator.validate(prompt_text)

        subfolder = self.storage.save_prompt(
            prompt_text=prompt_text,
            report=report,
            title="Projeto Mensageria",
            tags=["kafka", "python", "mensageria"],
            response_text="Resposta simulada com sucesso."
        )

        self.assertTrue(subfolder.exists())
        self.assertTrue(subfolder.is_dir())

        # Verifica presença dos arquivos
        prompt_file = subfolder / "prompt.md"
        report_file = subfolder / "validation_report.json"
        meta_file = subfolder / "metadata.json"
        resp_file = subfolder / "response.md"

        self.assertTrue(prompt_file.exists())
        self.assertTrue(report_file.exists())
        self.assertTrue(meta_file.exists())
        self.assertTrue(resp_file.exists())

        # Verifica conteúdo do prompt.md
        prompt_content = prompt_file.read_text(encoding="utf-8")
        self.assertIn("Projete a arquitetura", prompt_content)

        # Verifica conteúdo do metadata.json
        meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
        self.assertEqual(meta_data["title"], "Projeto Mensageria")
        self.assertEqual(meta_data["validation_status"], report.status.value)
        self.assertIn("kafka", meta_data["tags"])

        # Verifica listagem
        prompt_list = self.storage.list_saved_prompts()
        self.assertEqual(len(prompt_list), 1)
        self.assertEqual(prompt_list[0]["title"], "Projeto Mensageria")

        # Verifica get_prompt_details
        details = self.storage.get_prompt_details(subfolder.name)
        self.assertIsNotNone(details)
        self.assertIn("prompt_content", details)
        self.assertIn("response_content", details)


if __name__ == "__main__":
    unittest.main()
