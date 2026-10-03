# Missão 002 — Schemas versionados, redaction, idempotência e persistência confiável

## Objetivo

Transformar os contratos conceituais da Missão 001 em uma fundação persistente e verificável, sem
implementar o agente autônomo ou inferência real.

## Escopo

- Schemas JSON v1 para Project, Roadmap, Mission, Task, Action, Verification, Checkpoint,
  ResourceState, Capability, AuditEvent, BenchmarkResult e ModelBackend.
- Registry e validador mínimo, com compatibilidade explícita.
- Persistência JSON atômica compatível com Windows.
- Checkpoint formal, IDs determinísticos, UTC e lifecycle/idempotência.
- Redaction centralizada e audit event estruturado.
- Testes adversariais e documentação.
- Apache License 2.0.

## Fora de escopo

Agente completo, autonomia contínua, inferência, downloads, scheduler, executor irrestrito,
Resource Manager completo, browser, SSH, redes sociais, deploy e alterações em AFolha/TopazioAI.

## Critérios de aceite

- [x] Schemas possuem `schema_version` e são validados.
- [x] Versões futuras/desconhecidas são rejeitadas controladamente.
- [x] Persistência inválida não substitui o último estado válido.
- [x] Operações têm identidade determinística e repetição idempotente.
- [x] Checkpoint possui contrato verificável.
- [x] Redaction é aplicada a eventos e estruturas aninhadas.
- [x] Testes adversariais passam.
- [x] Scanner, Git, remoto e worktrees externos foram verificados.

## Rollback

Reverter o commit da Missão 002 preserva a baseline da Missão 001. Arquivos de estado locais não
são versionados e devem ser descartados somente por uma operação explícita de manutenção.

## Evidência

Ver `docs/audits/MISSION-002-REPORT.md`.
