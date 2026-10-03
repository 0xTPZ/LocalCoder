# Handoff operacional

Atualizado em 2026-10-03, Missão 001.

## Estado atual

`PASS` para a fundação local, documentação e testes descritos no relatório. `NOT TESTED` para
inferência, execução de comandos, scheduler, Resource Manager real, persistência durável,
integrações externas e recuperação após crash.

## O que existe

- Repositório em `E:\LocalCoder`.
- Pacote `src/localcoder` com contratos de modelo, recursos, capacidades, projeto, missão,
  checkpoints e auditoria.
- Testes determinísticos em `tests/test_foundation.py`.
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
- Não escolher licença pública sem decisão humana.

## Git e GitHub

O Git local é criado nesta missão. O GitHub CLI foi confirmado autenticado como `0xTPZ`; a criação
do repositório público depende da etapa explicitamente registrada no relatório e não deve ocorrer
com segredo no diff.

Commits locais atuais:

- `7bd942c0a8367ef0f4695ffc9b029c3e48a5a07f` — `feat: establish LocalCoder foundation`
- `ac02241d2d7d2624ce63f825de43b35033bbce04` — `docs: finalize Mission 001 evidence`
- `a3ee05aa7d370010f0c584a74109c77b52752f46` — `docs: record public repository handoff`

Repositório público: https://github.com/0xTPZ/LocalCoder. O primeiro push foi concluído em `main`.

## Próxima missão recomendada

Missão 002: schemas versionados para projeto, roadmap, missão, ação, resultado, checkpoint e
evento de auditoria, incluindo redaction e idempotência. Não começar pelo loop autônomo.
