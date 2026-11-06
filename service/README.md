# Camada de Serviço (`service`)

Esta pasta contém a lógica de negócio, casos de uso (*use cases*) e orquestrações da aplicação.

> [!IMPORTANT]
> **Atenção às Regras de Funcionamento da IA:**
> Conforme definido em [`service/RULES.md`](file:///home/walter/repos/architeture_studies_ai/service/RULES.md), esta pasta é estritamente particionada em **subpastas de domínio**. Nenhum arquivo de negócio pode ficar solto na raiz desta pasta.

---

## 📂 Subpastas de Domínio Ativas

- [`service/prompt_governance/`](file:///home/walter/repos/architeture_studies_ai/service/prompt_governance): Validação, filtros e scoring de prompts.
- [`service/audit_logging/`](file:///home/walter/repos/architeture_studies_ai/service/audit_logging): Persistência, auditoria e histórico de envios.
- [`service/model_interaction/`](file:///home/walter/repos/architeture_studies_ai/service/model_interaction): Casos de uso de interação e orquestração com modelos de IA.
