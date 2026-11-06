# Regras de Funcionamento e Governança de IA (AI Validation Rules)

Este documento define as **regras de funcionamento, critérios de validação e diretrizes operacionais** aplicadas a todas as interações com Inteligência Artificial no repositório `architecture_studies_ai`.

---

## 1. Visão Geral e Propósito

O objetivo deste diretório de validação é:
1. **Garantir a qualidade técnica e arquitetural** das entradas (prompts) enviadas às IAs.
2. **Impedir vazamento de dados sensíveis** (chaves de API, senhas, tokens ou dados pessoais).
3. **Auditar e rastrear todo o ciclo de vida dos prompts**, armazenando cada envio em uma subpasta dedicada com metadados e relatório de conformidade.
4. **Padronizar as expectativas de resposta da IA**, alinhadas com boas práticas de engenharia de software e arquitetura de sistemas.

---

## 2. Regras de Formulação de Prompts (Entrada)

Todo prompt direcionado à IA deve cumprir as seguintes regras:

### Regra 1: Clareza e Objetivo Explícito (RF-01)
- O prompt **deve** conter uma instrução clara e direta indicando qual tarefa a IA deve realizar (ex: analisar, refatorar, projetar, comparar trade-offs).
- Evite solicitações abertas ou ambíguas (ex: "o que você acha de microsserviços?"). Prefira: "Compare a adoção de microsserviços versus monolito modular sob a ótica de latência, governança de dados e custo de infraestrutura".

### Regra 2: Contexto Arquitetural Mínimo (RF-02)
- O prompt **deve** delimitar o contexto tecnológico e de negócios:
  - Linguagem/Ecossistema (ex: Python 3.12, Go, TypeScript).
  - Requisitos não-funcionais chave (ex: alta disponibilidade, baixa latência, conformidade com LGPD).
  - Restrições orçamentárias ou de infraestrutura (ex: Cloud-native AWS, On-premise, Serverless).

### Regra 3: Formato de Saída Especificado (RF-03)
- O prompt **deve** solicitar explicitamente como a resposta deve ser estruturada:
  - Exemplos: `Markdown estruturado com seções`, `Diagrama Mermaid`, `JSON Schema`, `Código com testes unitários`.

### Regra 4: Restrições Negativas e Limitações (RF-04)
- Quando relevante, o prompt deve declarar o que a IA **não** deve fazer (ex: "Não utilize dependências externas", "Não altere a assinatura pública da API", "Não assuma premissas não declaradas sem alertar").

---

## 3. Regras de Segurança e Conformidade (Restrições Rígidas)

Qualquer violação destas regras causará a **rejeição imediata** do envio:

### Regra 5: Proibição de Segredos e Credenciais (SEC-01) - *Bloqueante*
- É terminantemente proibido incluir nos prompts:
  - Chaves de API (ex: `sk-...`, `AKIA...`, `ghp_...`).
  - Tokens de autenticação (JWT, Bearer tokens).
  - Senhas, hashes ou chaves privadas SSH/TLS.
  - URLs internas sensíveis ou strings de conexão de banco de dados (`postgres://user:pass@host/db`).

### Regra 6: Proibição de Dados Pessoais / PII (SEC-02) - *Bloqueante*
- Não incluir nomes reais vinculados a documentos, números de CPF/SSN, cartões de crédito ou dados sensíveis de usuários reais. Utilize dados fictícios ou mascarados (ex: `usuario_teste@exemplo.com`).

---

## 4. Regras Operacionais para as Respostas da IA

Ao receber prompts validados, a IA deve operar sob as seguintes diretrizes:

1. **Rigor Arquitetural**: Priorizar princípios consolidados (SOLID, Clean Architecture, 12-Factor App, Domain-Driven Design).
2. **Análise de Trade-offs**: Nenhuma solução técnica é perfeita; a IA deve explicitar vantagens, desvantagens e custos de complexidade.
3. **Anti-alucinação**: Se os requisitos forem insuficientes para uma decisão arquitetural, a IA deve listar as premissas assumidas ou fazer perguntas de esclarecimento, nunca inventar fatos ou bibliotecas inexistentes.
4. **Pragmatismo**: Evitar sobre-engenharia (*over-engineering*). Preferir soluções simples e evolutivas.

---

## 5. Fluxo de Auditoria e Armazenamento em Subpastas

Para cada prompt enviado, o sistema de validação executa o seguinte fluxo automático:

```
[Prompt Enviado]
       │
       ▼
[Validador de Regras]
  ├── Checagem de Segurança (SEC-01, SEC-02) -> Se falhar: Rejeição ou Alerta
  ├── Análise de Qualidade (RF-01 a RF-04)    -> Cálculo de Score (0-100)
  └── Extração de Metadados
       │
       ▼
[Criação da Subpasta Exclusiva]
  Local: `ai_validation/prompts/YYYYMMDD_HHMMSS_<identificador>/`
  ├── prompt.md                 (Conteúdo integral do prompt)
  ├── metadata.json             (Data/hora, autor, contagem de palavras/tokens, tags)
  ├── validation_report.json    (Resultado da checagem de cada regra)
  └── response.md               (Opcional: Resposta gerada pela IA, se houver execução)
```

---

## 6. Critérios de Avaliação (Score de Qualidade)

Cada prompt recebe uma pontuação de 0 a 100 baseada no cumprimento das diretrizes:

| Critério | Peso | Descrição |
|---|---|---|
| **Segurança (Security Pass)** | Requisito | Se violar SEC-01 ou SEC-02, o prompt é bloqueado (Score 0) |
| **Objetivo Explícito** | 25 pts | Presença de verbos de comando e tarefa clara |
| **Contexto Técnico** | 25 pts | Menção a tecnologias, arquitetura ou requisitos |
| **Formato de Saída** | 20 pts | Definição do formato esperado para a resposta |
| **Escopo e Restrições** | 15 pts | Presença de limites claros ou restrições |
| **Comprimento Adequado** | 15 pts | Texto balanceado (evita prompts excessivamente telegráficos) |

- **Status Aprovado**: Score ≥ 70 e 0 violações de segurança.
- **Status Alerta / Atenção**: Score entre 40 e 69 (sugerida revisão, mas pode ser salvo/processado).
- **Status Reprovado**: Violação de segurança ou Score < 40.
