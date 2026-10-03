# Handoff operacional

Atualizado em 2026-10-03, Missão 002.

## Estado atual

`PASS` para a Missão 002: schemas v1, validador controlado, redaction, IDs estáveis, UTC,
idempotência, checkpoint formal, persistência JSON atômica e testes adversariais. `NOT TESTED`
para inferência, execução de comandos, scheduler, Resource Manager real, store especializado de
longa duração, integração externa e recuperação após crash do processo.

## O que existe

- Repositório em `E:\LocalCoder`.
- Pacote `src/localcoder` com contratos de modelo, recursos, capacidades, projeto, missão,
  checkpoints e auditoria.
- Testes determinísticos em `tests/test_foundation.py`.
- Schemas v1 em `schemas/v1/` e `SchemaRegistry` em `src/localcoder/schemas/`.
- `AtomicJsonStore` em `src/localcoder/persistence/`.
- Redaction, UTC, IDs, checkpoint e idempotência em `src/localcoder/state/`.
- Testes adversariais em `tests/test_mission002.py`.
- Scanner em `tools/check_secrets.py`.
- Roadmap e documentos de segurança/arquitetura/decisões.

## Comandos de verificação

```powershell
Set-Location E:\LocalCoder
python -m unittest discover -s tests -v
python tools\check_secrets.py
git diff --check
git status --short
```

## Limites importantes

- Não baixar modelos.
- Não alterar AFolha, TopazioAI ou outros projetos.
- Não ativar Task Scheduler, runtime de modelo ou servidor local.
- Licença: Apache License 2.0 em `LICENSE`.

## Git e GitHub

O GitHub CLI continua autenticado como `0xTPZ`; o repositório público existente é
https://github.com/0xTPZ/LocalCoder. O push da Missão 002 só ocorre após suíte, scanner, diff,
arquivos não rastreados, ausência de modelos/binários grandes e worktrees externos limpos.

Commits locais atuais:

- `7bd942c0a8367ef0f4695ffc9b029c3e48a5a07f` — `feat: establish LocalCoder foundation`
- `ac02241d2d7d2624ce63f825de43b35033bbce04` — `docs: finalize Mission 001 evidence`
- `a3ee05aa7d370010f0c584a74109c77b52752f46` — `docs: record public repository handoff`
- `941833a8d2cca8e4a4c67e6691b1d3cb391aefa8` — `feat: add versioned state persistence foundation`

Repositório público: https://github.com/0xTPZ/LocalCoder. O primeiro push foi concluído em `main`.

## Próxima missão recomendada

Missão 003: persistência especializada de checkpoints/audit trail e recuperação após crash usando
o primitive atômico da Missão 002. Não começar pelo loop autônomo.
