# LocalCoder

LocalCoder é um projeto open source em fundação para um agente local autônomo orientado a
projetos, roadmaps e missões. O mantenedor público é **0xTPZ**.

As Missões 001–003 formam a fundação: inventário, arquitetura, schemas versionados, validação,
redaction, IDs estáveis, UTC, idempotência, persistência JSON atômica, checkpoints duráveis,
journal, locking e recuperação segura. A Missão 004 adiciona Model Backend, Model Gateway,
structured output validado e o primeiro laboratório real local. O projeto ainda não implementa um
agente completo, não escolhe modelo definitivo, não executa comandos de projetos externos e não
ativa automação contínua.

## Estado da fundação

- Pacote Python 3.12 sem dependências de runtime obrigatórias.
- Contratos separados para backends de modelo, recursos, capacidades, projetos, missões,
  checkpoints e auditoria.
- Estados de Resource Manager previstos: `WORKING`, `PAUSING`, `SLEEPING`, `RESUMING`,
  `ERROR` e `WAITING`.
- Backend de modelo substituível; nenhum modelo é requisito do núcleo.
- Dados locais, logs e checkpoints ignorados pelo Git.
- Schemas JSON v1 para Project, Roadmap, Mission, Task, Action, Verification, Checkpoint,
  ResourceState, Capability, AuditEvent, BenchmarkResult e ModelBackend.
- Persistência atômica com validação antes da substituição, redaction centralizada e registry de
  idempotência.
- Checkpoint Store durável, Audit Store JSONL, journal operacional, lock conservador de arquivo e
  Recovery Manager fail-safe.
- Crash Lab com subprocessos reais para interrupção durante escrita e conflito de lock.
- Model Gateway com adapter HTTP OpenAI-compatible, configuração local-only e erros normalizados.
- Benchmark Harness v0 e laboratório real opt-in em `tools/run_model_lab.py`.
- Testes determinísticos da fundação e scanner heurístico de segredos.

## Começar

No PowerShell:

```powershell
Set-Location E:\LocalCoder
python -m unittest discover -s tests -v
python tools\check_secrets.py
python -m localcoder
```

Para usar o pacote como instalação editável em um ambiente isolado:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
```

Nenhum comando de desenvolvimento baixa modelos ou altera `E:\AFolha`, `E:\TopazioAI` ou outro
projeto. A instalação editável modifica somente o ambiente virtual local, que é ignorado pelo Git.

## Documentação

- [Arquitetura](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Decisões](docs/DECISIONS.md)
- [Segurança](docs/SECURITY.md)
- [Desenvolvimento](docs/DEVELOPMENT.md)
- [Constituição operacional](AGENTS.md)
- [Handoff](docs/HANDOFF.md)
- [Relatório da Missão 001](docs/audits/MISSION-001-REPORT.md)
- [Relatório da Missão 002](docs/audits/MISSION-002-REPORT.md)
- [Relatório da Missão 003](docs/audits/MISSION-003-REPORT.md)
- [Relatório da Missão 004](docs/audits/MISSION-004-REPORT.md)
- [Missão 003](docs/missions/003-durable-recovery.md)
- [Missão 004](docs/missions/004-model-gateway.md)
- [Configuração segura de gateway](configs/model-gateway.example.json)
- [Schemas](schemas/README.md)

## Licença

Este projeto é distribuído sob a [Apache License 2.0](LICENSE). O mantenedor público é `0xTPZ`.
