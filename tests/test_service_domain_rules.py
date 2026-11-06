"""
Testes unitários para as regras de delimitação de domínio na pasta service/.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from service.domain_checker import check_service_domains


class TestServiceDomainRules(unittest.TestCase):
    def test_current_service_directory_conforms_to_domain_rules(self):
        service_dir = Path(__file__).parent.parent / "service"
        is_valid, violations, domains = check_service_domains(service_dir)

        self.assertTrue(is_valid, f"Violações encontradas em service/: {violations}")
        self.assertEqual(len(violations), 0)
        self.assertIn("prompt_governance", domains)
        self.assertIn("audit_logging", domains)
        self.assertIn("model_interaction", domains)

    def test_rejects_loose_file_in_service_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_service = Path(tmp) / "service"
            tmp_service.mkdir()
            (tmp_service / "__init__.py").touch()
            (tmp_service / "unauthorized_service.py").touch()

            is_valid, violations, _ = check_service_domains(tmp_service)
            self.assertFalse(is_valid)
            self.assertTrue(any("unauthorized_service.py" in v for v in violations))

    def test_rejects_domain_subfolder_without_init(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_service = Path(tmp) / "service"
            tmp_service.mkdir()
            (tmp_service / "__init__.py").touch()
            domain_sub = tmp_service / "billing_domain"
            domain_sub.mkdir()
            (domain_sub / "charge_card.py").touch()

            is_valid, violations, _ = check_service_domains(tmp_service)
            self.assertFalse(is_valid)
            self.assertTrue(any("billing_domain" in v and "__init__.py" in v for v in violations))


if __name__ == "__main__":
    unittest.main()
