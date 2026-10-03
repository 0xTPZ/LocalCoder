# Missão 003 — Checkpoints duráveis, locking, journal e recuperação após crash

## Objetivo

Construir a primeira camada durável do LocalCoder sem conectar LLM real, executar ações externas
ou implementar autonomia contínua.

## Escopo

- `CheckpointStore` especializado sobre schemas v1 e `AtomicJsonStore`.
- `AuditStore` JSONL append-only com redaction, sequência e deduplicação.
- `JournalStore` para planned/started/paused/completed/failed.
- `FileLock` para proteger estado local entre instâncias.
- `RecoveryManager` somente leitura com classificação fail-safe.
- Crash Lab com subprocessos reais e cenários adversariais.
- Documentação de pause/resume e limitações.

## Fora de escopo

LLM, executor de comandos, scheduler, Resource Manager completo, browser, SSH, APIs, publicação,
Git automation, locking distribuído, backup remoto e repetição automática de ações.

## Riscos

- Lock stale removido incorretamente pode permitir dois escritores.
- JSONL parcialmente escrito pode esconder uma decisão se tolerância for ampla demais.
- `ACTION_STARTED` pode ter produzido efeito externo desconhecido.
- PID reuse e processos encerrados exigem verificação nativa no Windows.

## Critérios de aceite

- [x] Checkpoint Store funcional, validado e protegido por lock.
- [x] Audit Store append-only com redaction e ordenação reconstruível.
- [x] Journal detecta operação sem terminal.
- [x] Lock concorrente testado e stale não removido automaticamente.
- [x] Recovery classifica clean/recoverable/ambiguous/corrupted/blocked.
- [x] Operação ambígua não é repetida automaticamente.
- [x] Crash Lab usa subprocessos próprios e diretórios temporários.
- [x] Testes anteriores continuam passando.
- [x] AFolha/TopazioAI não são modificados.

## Rollback

Reverter os commits da missão retorna à camada da Missão 002. Temporários de estado nunca são
promovidos automaticamente; a recuperação deve preservar o arquivo principal válido até decisão
explícita.

## Evidência

Ver `docs/audits/MISSION-003-REPORT.md`.
