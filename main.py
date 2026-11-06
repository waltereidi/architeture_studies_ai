#!/usr/bin/env python3
"""
CLI Principal: Validação de Prompts e Armazenamento em Subpastas.

Uso:
    python main.py "Seu prompt aqui"
    python main.py --file caminho/do/prompt.txt
    python main.py --interactive
    python main.py --list
    python main.py --show <nome_da_subpasta>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from ai_validation.validator import PromptValidator, ValidationStatus
from ai_validation.storage import PromptStorage
from service.domain_checker import check_service_domains, detect_git_changes_in_service


def print_banner() -> None:
    print("=" * 70)
    print("   AI VALIDATION SETUP - Architecture Studies")
    print("   Governança, Regras de Funcionamento e Auditoria de Prompts")
    print("=" * 70)


def format_report_output(report, subfolder_path: Optional[Path] = None) -> None:
    status_icons = {
        ValidationStatus.APPROVED: "[✓ APROVADO]",
        ValidationStatus.WARNING: "[! AVISO]",
        ValidationStatus.REJECTED: "[✗ REPROVADO]",
    }

    icon = status_icons.get(report.status, "[?]")
    print(f"\nResultado da Validação: {icon} - Status: {report.status.value}")
    print(f"Pontuação de Qualidade: {report.score}/100\n")

    print("Critérios Avaliados:")
    for item in report.quality_breakdown:
        mark = "✓" if item.passed else "✗"
        print(f"  [{mark}] {item.criterion:<30} ({item.score:>2}/{item.max_score} pts) -> {item.details}")

    if report.violations:
        print("\nViolações Encontradas:")
        for v in report.violations:
            print(f"  - [{v.severity}] {v.rule_name} ({v.rule_id}): {v.message}")

    if report.suggestions:
        print("\nSugestões de Melhoria:")
        for s in report.suggestions:
            print(f"  * {s}")

    if subfolder_path:
        print(f"\nPrompt e Auditoria salvos na subpasta:")
        print(f"  -> {subfolder_path.resolve()}")
        print(f"     Arquivos: prompt.md | metadata.json | validation_report.json")
    print("-" * 70)


def handle_process_prompt(
    prompt_text: str,
    title: Optional[str],
    tags: Optional[List[str]],
    check_only: bool,
    simulate_response: bool,
    author: Optional[str]
) -> int:
    validator = PromptValidator()
    storage = PromptStorage()

    print("\nExecutando checagem das regras de funcionamento...")
    report = validator.validate(prompt_text)

    response_text = None
    if simulate_response and report.is_valid:
        response_text = (
            "### Resposta Simulada da IA\n\n"
            "Esta é uma resposta gerada em modo de simulação para validação de fluxo.\n"
            "O prompt atendeu aos critérios arquiteturais estipulados nas regras."
        )

    subfolder = None
    if not check_only:
        subfolder = storage.save_prompt(
            prompt_text=prompt_text,
            report=report,
            title=title,
            tags=tags,
            response_text=response_text,
            author=author,
        )

    format_report_output(report, subfolder)
    return 0 if report.is_valid else 1


def handle_list() -> None:
    storage = PromptStorage()
    items = storage.list_saved_prompts()
    print_banner()
    print(f"\nTotal de prompts arquivados: {len(items)}\n")
    if not items:
        print("Nenhum prompt foi salvo até o momento.")
        return

    print(f"{'Data/Hora':<20} | {'Status':<10} | {'Score':<5} | {'Título / Subpasta'}")
    print("-" * 70)
    for it in items:
        created = it.get("created_at", "")[:19].replace("T", " ")
        status = it.get("validation_status", "N/A")
        score = it.get("validation_score", 0)
        title = it.get("title") or it.get("subfolder")
        subfolder = it.get("subfolder")
        print(f"{created:<20} | {status:<10} | {score:>3}/100 | {title} ({subfolder})")
    print("-" * 70)


def handle_show(subfolder_name: str) -> None:
    storage = PromptStorage()
    details = storage.get_prompt_details(subfolder_name)
    if not details:
        print(f"Erro: Subpasta '{subfolder_name}' não encontrada em {storage.base_dir}")
        sys.exit(1)

    print_banner()
    print(f"Detalhes do Registro: {subfolder_name}")
    print(f"Caminho: {details['path']}\n")

    if "metadata" in details:
        meta = details["metadata"]
        print(f"Título: {meta.get('title')}")
        print(f"Data: {meta.get('created_at')}")
        print(f"Status: {meta.get('validation_status')} (Score: {meta.get('validation_score')}/100)")
        print(f"Caracteres: {meta.get('character_count')} | Palavras: {meta.get('word_count')}")
        if meta.get("tags"):
            print(f"Tags: {', '.join(meta.get('tags'))}")

    if "prompt_content" in details:
        print("\n" + "=" * 30 + " PROMPT " + "=" * 30)
        print(details["prompt_content"])

    if "response_content" in details:
        print("\n" + "=" * 30 + " RESPOSTA DA IA " + "=" * 30)
        print(details["response_content"])


def handle_check_service() -> int:
    service_dir = Path("service")
    is_valid, violations, domains = check_service_domains(service_dir)
    changed_files = detect_git_changes_in_service(Path("."))

    print_banner()
    print("\nAuditoria de Delimitação de Domínio da Pasta 'service/':\n")

    if changed_files:
        print("Modificações recentes detectadas via Git em 'service/':")
        for cf in changed_files:
            print(f"  * {cf}")
        print()
    else:
        print("Nenhuma modificação não commitada detectada em 'service/'.\n")

    print(f"Subpastas de Domínio Cadastradas ({len(domains)}):")
    for dom, files in sorted(domains.items()):
        print(f"  📁 service/{dom}/ ({len(files)} arquivos)")
        for fl in files[:3]:
            print(f"      - {fl}")
        if len(files) > 3:
            print(f"      ... e mais {len(files) - 3} arquivos")

    if violations:
        print("\n[✗ VIOLAÇÕES ENCONTRADAS]:")
        for v in violations:
            print(f"  - {v}")
        print("\nFalha: Arquivos soltos ou domínios sem __init__.py identificados.")
        return 1

    print("\n[✓ CONFORME]: Toda lógica em 'service/' está devidamente encapsulada em subpastas de domínio.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sistema de Validação de Regras de Funcionamento e Histórico de Prompts para IA."
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Texto do prompt a ser validado e salvo."
    )
    parser.add_argument(
        "-f", "--file",
        type=Path,
        help="Caminho para arquivo de texto contendo o prompt."
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Digitar o prompt em modo interativo."
    )
    parser.add_argument(
        "-t", "--title",
        type=str,
        help="Título ou assunto do prompt para identificação da subpasta."
    )
    parser.add_argument(
        "--tags",
        type=str,
        help="Tags separadas por vírgula (ex: 'arquitetura,microsservicos,api')."
    )
    parser.add_argument(
        "--author",
        type=str,
        default="developer",
        help="Nome ou identificador do autor do prompt."
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Apenas valida o prompt contra as regras sem salvar em subpasta."
    )
    parser.add_argument(
        "--simulate-response",
        action="store_true",
        help="Simula e anexa uma resposta no arquivo response.md dentro da subpasta."
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="Lista todos os prompts salvos em subpastas."
    )
    parser.add_argument(
        "-s", "--show",
        type=str,
        help="Exibe os detalhes de uma subpasta de prompt específica."
    )
    parser.add_argument(
        "--check-service",
        action="store_true",
        help="Audita a pasta service/ e valida se todas as alterações pertencem a subpastas de domínio."
    )

    args = parser.parse_args()

    if args.check_service:
        sys.exit(handle_check_service())

    if args.list:
        handle_list()
        return

    if args.show:
        handle_show(args.show)
        return

    prompt_text = ""
    if args.file:
        if not args.file.exists():
            print(f"Erro: Arquivo '{args.file}' não foi encontrado.", file=sys.stderr)
            sys.exit(1)
        prompt_text = args.file.read_text(encoding="utf-8")
    elif args.interactive:
        print_banner()
        print("Digite seu prompt abaixo (Pressione Ctrl+D ou digite EOF em uma linha vazia para finalizar):\n")
        lines = []
        try:
            while True:
                line = input()
                if line.strip() == "EOF":
                    break
                lines.append(line)
        except EOFError:
            pass
        prompt_text = "\n".join(lines)
    elif args.prompt:
        prompt_text = args.prompt
    else:
        print_banner()
        parser.print_help()
        sys.exit(0)

    if not prompt_text.strip():
        print("Erro: O prompt fornecido está vazio.", file=sys.stderr)
        sys.exit(1)

    print_banner()
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []

    exit_code = handle_process_prompt(
        prompt_text=prompt_text,
        title=args.title,
        tags=tags,
        check_only=args.check_only,
        simulate_response=args.simulate_response,
        author=args.author,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
