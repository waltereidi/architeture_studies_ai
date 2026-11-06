# Architecture Studies AI - Setup de Validação e Auditoria de Prompts

Este repositório possui uma arquitetura com uma **pasta de validação direcionada à Inteligência Artificial**, contendo **regras de funcionamento** explícitas e um mecanismo automatizado que **armazena cada prompt enviado em uma subpasta individual**, acompanhado de metadados e relatório de conformidade.

---

## 📁 Estrutura do Setup

```text
architeture_studies_ai/
├── ai_validation/                         # 🛡️ Pasta de validação direcionada à IA
│   ├── RULES.md                           # Regras de funcionamento, governança e diretrizes para a IA
│   ├── rules_config.json                  # Configurações programáticas (limites, regex de segurança, pesos)
│   ├── validator.py                       # Mecanismo validador (regras de segurança, clareza e score)
│   ├── storage.py                         # Gerenciador de armazenamento em subpastas
│   └── prompts/                           # 📂 Subpastas onde cada prompt enviado é armazenado
│       ├── .gitkeep
│       └── YYYYMMDD_HHMMSS_<slug>_<id>/   # Subpasta única por prompt
│           ├── prompt.md                  # Conteúdo original do prompt enviado
│           ├── metadata.json              # Data/hora, autor, tags, contagem de palavras/caracteres
│           ├── validation_report.json     # Relatório detalhado com score e checagem de regras
│           └── response.md                # (Opcional) Resposta gerada pela IA
├── tests/
│   └── test_validation.py                 # Testes unitários do validador e persistência
├── main.py                                # CLI executável para envio, validação e auditoria
├── .gitignore
└── README.md
```

---

## 📜 Regras de Funcionamento da IA

As regras completas estão documentadas em [`ai_validation/RULES.md`](file:///home/walter/repos/architeture_studies_ai/ai_validation/RULES.md). As principais diretrizes são:

1. **Objetivo Explícito (RF-01):** O prompt deve conter verbos de ação claros (`analisar`, `projetar`, `comparar`, `implementar`).
2. **Contexto Arquitetural Mínimo (RF-02):** Especificar tecnologias, linguagens, arquitetura ou requisitos não-funcionais (Clean Architecture, microsserviços, latência, etc.).
3. **Formato de Saída (RF-03):** Indicar a estrutura da resposta esperada (`Markdown`, `JSON`, `Diagrama Mermaid`, `Tabela`).
4. **Restrições e Limitações (RF-04):** Declarar o que a IA **não** deve fazer para evitar alucinações e sobre-engenharia.
5. **Segurança e Sigilo (SEC-01 / SEC-02 - Bloqueante):** É proibido o envio de credenciais, chaves de API (`sk-...`, `AKIA...`), tokens JWT ou dados sensíveis (PII). Prompts com violações de segurança são sumariamente reprovados.

---

## 🚀 Como Utilizar

O setup inclui a CLI [`main.py`](file:///home/walter/repos/architeture_studies_ai/main.py) pronta para uso com Python 3 (sem dependências externas):

### 1. Enviar um prompt via linha de comando
```bash
python3 main.py "Analise a arquitetura de microsserviços em Python e Postgres. Apresente os trade-offs em formato Markdown e tabela. Não assuma infraestrutura em nuvem proprietária." --title "Estudo Microsserviços" --tags "arquitetura,python,postgres"
```

### 2. Enviar prompt a partir de um arquivo
```bash
python3 main.py --file caminho/do/meu_prompt.txt --title "Refatoração de API"
```

### 3. Modo interativo
```bash
python3 main.py --interactive
```

### 4. Simular recebimento de resposta da IA
```bash
python3 main.py "Projete uma API REST em Go com Clean Architecture. Formato Markdown. Sem libs externas." --simulate-response
```

### 5. Listar todos os prompts arquivados
```bash
python3 main.py --list
```

### 6. Consultar os detalhes de um prompt arquivado
```bash
python3 main.py --show <nome_da_subpasta>
```

---

## 📊 Estrutura de Cada Subpasta de Prompt

Para cada prompt enviado, o sistema gera automaticamente uma subpasta em `ai_validation/prompts/` com o padrão:
`YYYYMMDD_HHMMSS_<slug>_<hash>`:

Exemplo de conteúdo salvo:

### `metadata.json`
```json
{
  "id": "8f9afa4e",
  "subfolder": "20261106_194837_estudo_microsserviços_e_postgr_8f9afa4e",
  "created_at": "2026-11-06T19:48:37.604968",
  "author": "developer",
  "title": "Estudo Microsserviços e Postgres",
  "tags": ["arquitetura", "microsservicos", "postgres"],
  "character_count": 164,
  "word_count": 23,
  "validation_status": "APPROVED",
  "validation_score": 100,
  "is_valid": true,
  "files": {
    "prompt": "prompt.md",
    "validation_report": "validation_report.json",
    "response": "response.md"
  }
}
```

### `validation_report.json`
```json
{
  "is_valid": true,
  "status": "APPROVED",
  "score": 100,
  "violations": [],
  "quality_breakdown": [
    {
      "criterion": "Objetivo Explícito",
      "score": 25,
      "max_score": 25,
      "passed": true,
      "details": "Verbos identificados: analise"
    },
    {
      "criterion": "Contexto Técnico / Arquitetura",
      "score": 25,
      "max_score": 25,
      "passed": true,
      "details": "Termos técnicos encontrados: arquitetura, microsserviços, postgres, python"
    }
  ],
  "suggestions": []
}
```

---

## 🧪 Executando os Testes Automatizados

Para rodar a suíte de testes unitários:

```bash
python3 -m unittest discover tests
```
