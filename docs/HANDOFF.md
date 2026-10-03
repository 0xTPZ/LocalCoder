# Handoff operacional

Atualizado em 2026-10-03, Missão 003.

## Estado atual

`PASS` para a implementação da Missão 003 em validação local: Checkpoint Store, Audit Store,
journal, locking conservador, Recovery Manager e Crash Lab. `NOT TESTED` para inferência,
execução de comandos, scheduler, Resource Manager real, locking distribuído, backup remoto e
recuperação de ações externas reais.

## O que existe

- Repositório em `E:\LocalCoder`.
- Pacote `src/localcoder` com contratos de modelo, recursos, capacidades, projeto, missão,
  checkpoints e auditoria.
- Testes determinísticos em `tests/test_foundation.py`.
- Schemas v1 em `schemas/v1/` e `SchemaRegistry` em `src/localcoder/schemas/`.
- `AtomicJsonStore` em `src/localcoder/persistence/`.
- Redaction, UTC, IDs, checkpoint e idempotência em `src/localcoder/state/`.
- Testes adversariais em `tests/test_mission002.py`.
- `CheckpointStore` em `src/localcoder/checkpoints/store.py`.
- `AuditStore` em `src/localcoder/audit/store.py`.
- `JournalStore` em `src/localcoder/mission_engine/journal.py`.
- `FileLock`/JSONL em `src/localcoder/persistence/`.
- `RecoveryManager` em `src/localcoder/recovery/`.
- Crash Lab em `tests/test_mission003.py` e `tests/crash_helpers.py`.
- Scanner em `tools/check_secrets.py`.
- Roadmap e documentos de segurança/arquitetura/decisões.

## Comandos de verificação

```powershell
Set-Location E:\LocalCoder
python -m unittest discover -s tests -v
python tools\check_secrets.py
python -m compileall -q src tests tools
git diff --check
git status --short
```

## Limites importantes

- Não baixar modelos.
- Não alterar AFolha, TopazioAI ou outros projetos.
- Não ativar Task Scheduler, runtime de modelo ou servidor local.
- Licença: Apache License 2.0 em `LICENSE`.
- Nenhuma ação externa é repetida automaticamente após `ACTION_STARTED` sem terminal; o recovery
  classifica `AMBIGUOUS` e aguarda decisão humana.

## Git e GitHub

O GitHub CLI continua autenticado como `0xTPZ`; o repositório público existente é
https://github.com/0xTPZ/LocalCoder. O push da Missão 003 só ocorre após suíte, scanner, diff,
arquivos não rastreados, ausência de modelos/binários grandes e worktrees externos limpos.

Commits locais atuais:

- `7bd942c0a8367ef0f4695ffc9b029c3e48a5a07f` — `feat: establish LocalCoder foundation`
- `ac02241d2d7d2624ce63f825de43b35033bbce04` — `docs: finalize Mission 001 evidence`
- `a3ee05aa7d370010f0c584a74109c77b52752f46` — `docs: record public repository handoff`
- `941833a8d2cca8e4a4c67e6691b1d3cb391aefa8` — `feat: add versioned state persistence foundation`
- `14a5892460cba1be6996e5598abd89745e9070c0` — `docs: finalize Mission 002 evidence`
- `5382c08` — `feat: add durable checkpoint recovery`

O commit documental final da Missão 003 será adicionado após a validação desta atualização.

Repositório público: https://github.com/0xTPZ/LocalCoder. O primeiro push foi concluído em `main`.
O push da Missão 002 também foi concluído sem force push; `HEAD` e `origin/main` coincidem.
No início da Missão 003, AFolha e TopazioAI estavam limpos. A Missão 003 não alterou nenhum
projeto externo; o gate final deve confirmar ambos novamente.

## Próxima missão recomendada

Missão 004: ingestão segura de projeto sem execução automática, com root canônico, limites e
proteção contra path traversal/prompt injection. Não começar pelo loop autônomo.
