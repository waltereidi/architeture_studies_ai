"""
Validador de regras de funcionamento para prompts de IA.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ValidationStatus(str, Enum):
    APPROVED = "APPROVED"       # Atende aos critérios de qualidade e segurança
    WARNING = "WARNING"         # Contém avisos de qualidade, mas seguro
    REJECTED = "REJECTED"       # Violou regras críticas ou qualidade insuficiente


@dataclass
class RuleViolation:
    rule_id: str
    rule_name: str
    message: str
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"


@dataclass
class QualityItem:
    criterion: str
    score: int
    max_score: int
    passed: bool
    details: str


@dataclass
class ValidationReport:
    is_valid: bool
    status: ValidationStatus
    score: int  # 0 a 100
    violations: List[RuleViolation] = field(default_factory=list)
    quality_breakdown: List[QualityItem] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "status": self.status.value,
            "score": self.score,
            "violations": [asdict(v) for v in self.violations],
            "quality_breakdown": [asdict(q) for q in self.quality_breakdown],
            "suggestions": self.suggestions,
        }


class PromptValidator:
    """Valida prompts de acordo com as regras de funcionamento estabelecidas."""

    DEFAULT_CONFIG_PATH = Path(__file__).parent / "rules_config.json"

    def __init__(self, config_path: Optional[Path] = None):
        target_path = config_path or self.DEFAULT_CONFIG_PATH
        if target_path.exists():
            with open(target_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            self.config = self._fallback_config()

        self._compile_security_patterns()

    def _compile_security_patterns(self) -> None:
        self.compiled_secrets = []
        for sec in self.config.get("security", {}).get("secret_patterns", []):
            try:
                regex = re.compile(sec["pattern"], re.IGNORECASE)
                self.compiled_secrets.append({
                    "name": sec["name"],
                    "severity": sec.get("severity", "CRITICAL"),
                    "regex": regex
                })
            except re.error:
                continue

    def _fallback_config(self) -> Dict[str, Any]:
        return {
            "limits": {"min_characters": 30, "max_characters": 100000, "min_words": 5},
            "security": {"block_on_secret": true, "secret_patterns": []},
            "quality_checks": {
                "action_verbs": ["analisar", "criar", "implementar", "comparar"],
                "context_keywords": ["arquitetura", "api", "sistema", "python"],
                "output_format_keywords": ["markdown", "json", "tabela"],
                "constraint_keywords": ["não", "apenas", "deve", "sem"]
            },
            "scoring_weights": {
                "action_goal": 25,
                "technical_context": 25,
                "output_format": 20,
                "constraints": 15,
                "adequate_length": 15
            }
        }

    def validate(self, prompt_text: str) -> ValidationReport:
        """Executa todas as checagens e retorna um relatório de validação completo."""
        text = prompt_text.strip()
        violations: List[RuleViolation] = []
        quality_breakdown: List[QualityItem] = []
        suggestions: List[str] = []

        limits = self.config.get("limits", {})
        min_chars = limits.get("min_characters", 30)
        max_chars = limits.get("max_characters", 100000)
        min_words = limits.get("min_words", 5)

        char_count = len(text)
        words = re.findall(r"\b[\w-]+\b", text.lower())
        word_count = len(words)

        # 1. Checagem de Limites
        if char_count < min_chars or word_count < min_words:
            violations.append(RuleViolation(
                rule_id="LEN-01",
                rule_name="Comprimento Mínimo",
                message=f"Prompt muito curto ({char_count} chars, {word_count} palavras). Mínimo esperado: {min_chars} chars e {min_words} palavras.",
                severity="HIGH"
            ))
            suggestions.append("Detalhe melhor o objetivo, contexto e o que você espera que a IA produza.")

        if char_count > max_chars:
            violations.append(RuleViolation(
                rule_id="LEN-02",
                rule_name="Comprimento Máximo",
                message=f"Prompt excede o limite máximo configurado ({char_count} > {max_chars}).",
                severity="HIGH"
            ))
            suggestions.append("Considere dividir o prompt em etapas menores ou modularizar os requisitos.")

        # 2. Checagem de Segurança (Secrets / Chaves / Senhas)
        has_critical_security_violation = False
        for sec in self.compiled_secrets:
            match = sec["regex"].search(text)
            if match:
                violations.append(RuleViolation(
                    rule_id="SEC-01",
                    rule_name=f"Vazamento de Segredo: {sec['name']}",
                    message=f"Detectado potencial segredo/credencial correspondente a '{sec['name']}'.",
                    severity=sec["severity"]
                ))
                has_critical_security_violation = True
                suggestions.append("Remova chaves de API, senhas, tokens de autenticação ou hashes do prompt.")

        # 3. Análise de Qualidade de Engenharia de Prompt
        weights = self.config.get("scoring_weights", {})
        checks = self.config.get("quality_checks", {})
        total_score = 0

        # a) Objetivo Explícito (Verbos de ação)
        action_verbs = checks.get("action_verbs", [])
        found_actions = [v for v in action_verbs if v in text.lower()]
        action_weight = weights.get("action_goal", 25)
        action_passed = len(found_actions) > 0
        if action_passed:
            total_score += action_weight
            quality_breakdown.append(QualityItem(
                criterion="Objetivo Explícito",
                score=action_weight,
                max_score=action_weight,
                passed=True,
                details=f"Verbos identificados: {', '.join(found_actions[:3])}"
            ))
        else:
            quality_breakdown.append(QualityItem(
                criterion="Objetivo Explícito",
                score=0,
                max_score=action_weight,
                passed=False,
                details="Nenhum verbo de ação ou comando explícito identificado."
            ))
            suggestions.append("Inclua um verbo de ação claro (ex: analise, crie, compare, projete, implemente).")

        # b) Contexto Técnico / Arquitetural
        context_keywords = checks.get("context_keywords", [])
        found_contexts = [k for k in context_keywords if k in text.lower()]
        context_weight = weights.get("technical_context", 25)
        context_passed = len(found_contexts) > 0
        if context_passed:
            total_score += context_weight
            quality_breakdown.append(QualityItem(
                criterion="Contexto Técnico / Arquitetura",
                score=context_weight,
                max_score=context_weight,
                passed=True,
                details=f"Termos técnicos encontrados: {', '.join(found_contexts[:4])}"
            ))
        else:
            quality_breakdown.append(QualityItem(
                criterion="Contexto Técnico / Arquitetura",
                score=0,
                max_score=context_weight,
                passed=False,
                details="Pouco ou nenhum contexto arquitetural/tecnológico mencionado."
            ))
            suggestions.append("Especifique o contexto técnico (ex: Python, microsserviços, Clean Architecture, Docker).")

        # c) Formato de Saída Especificado
        format_keywords = checks.get("output_format_keywords", [])
        found_formats = [f for f in format_keywords if f in text.lower()]
        format_weight = weights.get("output_format", 20)
        format_passed = len(found_formats) > 0
        if format_passed:
            total_score += format_weight
            quality_breakdown.append(QualityItem(
                criterion="Formato de Saída",
                score=format_weight,
                max_score=format_weight,
                passed=True,
                details=f"Formato solicitado: {', '.join(found_formats[:3])}"
            ))
        else:
            quality_breakdown.append(QualityItem(
                criterion="Formato de Saída",
                score=0,
                max_score=format_weight,
                passed=False,
                details="Nenhum formato de resposta foi expressamente solicitado."
            ))
            suggestions.append("Defina o formato de resposta desejado (ex: Markdown, JSON, Diagrama Mermaid, Tabela).")

        # d) Restrições e Limites
        constraint_keywords = checks.get("constraint_keywords", [])
        found_constraints = [c for c in constraint_keywords if c in text.lower()]
        constraint_weight = weights.get("constraints", 15)
        constraint_passed = len(found_constraints) > 0
        if constraint_passed:
            total_score += constraint_weight
            quality_breakdown.append(QualityItem(
                criterion="Restrições e Escopo",
                score=constraint_weight,
                max_score=constraint_weight,
                passed=True,
                details=f"Diretrizes/Restrições identificadas."
            ))
        else:
            quality_breakdown.append(QualityItem(
                criterion="Restrições e Escopo",
                score=0,
                max_score=constraint_weight,
                passed=False,
                details="Nenhuma restrição ou limitação explícita identificada."
            ))
            suggestions.append("Se aplicável, defina o que NÃO fazer (ex: 'sem bibliotecas externas', 'não invente requisitos').")

        # e) Extensão e Completude do Prompt
        length_weight = weights.get("adequate_length", 15)
        if char_count >= min_chars and word_count >= min_words:
            total_score += length_weight
            quality_breakdown.append(QualityItem(
                criterion="Extensão Adequada",
                score=length_weight,
                max_score=length_weight,
                passed=True,
                details=f"{char_count} caracteres, {word_count} palavras."
            ))
        else:
            quality_breakdown.append(QualityItem(
                criterion="Extensão Adequada",
                score=0,
                max_score=length_weight,
                passed=False,
                details=f"Abaixo do mínimo recomendado."
            ))

        # 4. Decisão de Status
        if has_critical_security_violation:
            status = ValidationStatus.REJECTED
            is_valid = False
            total_score = 0  # Rejeição imediata por violação de segurança
        elif total_score >= 70 and not any(v.severity in ("CRITICAL", "HIGH") for v in violations):
            status = ValidationStatus.APPROVED
            is_valid = True
        elif total_score >= 40 and not any(v.severity == "CRITICAL" for v in violations):
            status = ValidationStatus.WARNING
            is_valid = True
        else:
            status = ValidationStatus.REJECTED
            is_valid = False

        return ValidationReport(
            is_valid=is_valid,
            status=status,
            score=total_score,
            violations=violations,
            quality_breakdown=quality_breakdown,
            suggestions=suggestions
        )
