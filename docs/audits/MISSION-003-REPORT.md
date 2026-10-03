# Relatório final — Missão 003

Data: 2026-10-03. Mantenedor: `0xTPZ`.

## 1. Status geral

`PASS` para a implementação e os testes da camada durável local. Foram implementados Checkpoint
Store, Audit Store, journal operacional, locking conservador, Recovery Manager e Crash Lab. Não
há LLM real, executor de ações externas, scheduler ou repetição automática.

## 2. Arquitetura implementada

```text
CheckpointRecord → CheckpointStore → FileLock + AtomicJsonStore → checkpoint/*.json
AuditEvent      → AuditStore      → FileLock + JSONL/fsync   → audit.jsonl
Action facts    → JournalStore    → FileLock + JSONL/fsync   → journal.jsonl
                                      ↓
                              RecoveryManager.inspect()
                                      ↓
                    CLEAN / RECOVERABLE / AMBIGUOUS / CORRUPTED / BLOCKED
```

O Recovery Manager só inspeciona, valida, reconstrói e classifica. Não executa comandos, não
promove temporários e não repete operações.

## 3. Estratégia de checkpoint

`CheckpointStore` encapsula arquivos e usa o schema `checkpoint` v1. `create` não sobrescreve,
`replace` exige arquivo existente, `get`, `enumerate`, `validate` e `active` validam todos os
documentos. Um lock por diretório serializa escritores. Temporários abandonados são listados pelo
Recovery Manager e o principal válido permanece autoritativo.

## 4. Estratégia de audit trail

`AuditStore` grava uma linha JSON redigida por evento, com `sequence` monotônica, `correlation_id`,
timestamp UTC e `fsync`. `event_id` torna append repetido idempotente. Apenas o último registro
com falha de decodificação é ignorado com diagnóstico; schema inválido, versão desconhecida ou
corrupção em registro anterior gera corrupção do journal/audit.

## 5. Estratégia de journal

`JournalStore` registra `ACTION_PLANNED`, `ACTION_STARTED`, `ACTION_PAUSED`, `ACTION_COMPLETED` e
`ACTION_FAILED`, com `operation_id`, `action_id`, sequência e dados redigidos. O último estado
não terminal `STARTED`/`PAUSED` é `AMBIGUOUS`; a recuperação recomenda
`STOP_AND_REQUEST_HUMAN_DECISION`.

## 6. Estratégia de locking

`FileLock` cria exclusivamente um arquivo de metadados com `O_CREAT|O_EXCL`, PID, host, lock_id e
timestamp. Conflito falha imediatamente. Liberação verifica ownership. Stale não é removido
automaticamente; `release_stale` exige lock_id esperado e PID comprovadamente morto. No Windows,
`OpenProcess`/`GetExitCodeProcess` substitui a sondagem não confiável de `os.kill(pid, 0)`.

## 7. Estratégia de recovery

`RecoveryManager.inspect()` verifica locks vivos, checkpoints, temporários, journal e audit. Os
resultados são:

- `CLEAN`: nenhum estado pendente ou ambíguo;
- `RECOVERABLE`: checkpoint válido/temporário abandonado ou cauda truncada, sem ambiguidade;
- `AMBIGUOUS`: operação iniciada/pausada sem terminal;
- `CORRUPTED`: checkpoint, journal ou audit não validável;
- `BLOCKED`: lock vivo impede conclusão segura da inspeção operacional.

Em `AMBIGUOUS`, `safe_to_resume` é falso e nenhuma ação é reenfileirada.

## 8. Resultados do Crash Lab

| Cenário | Resultado |
|---|---|
| morte antes da gravação | `PASS`: nenhum falso evento/estado foi criado |
| morte durante temporário | `PASS`: subprocesso saiu com código 71; principal permaneceu válido |
| temporário abandonado | `PASS`: detectado; não promovido |
| principal válido | `PASS`: leitura após crash preservou estado |
| último journal truncado | `PASS`: cauda ignorada com diagnóstico |
| `ACTION_STARTED` sem terminal | `PASS`: `AMBIGUOUS`, sem auto-repeat |
| duas instâncias no mesmo lock | `PASS`: segunda aquisição rejeitada |
| lock stale | `PASS`: remoção só após PID morto + lock_id |
| lock vivo durante recovery | `PASS`: `BLOCKED`, sem retomada |
| múltiplos checkpoints ativos | `PASS`: `AMBIGUOUS`, sem retomada |
| restart após concluída | `PASS`: `CLEAN`, sem operação ambígua |
| restart após ambígua | `PASS`: `AMBIGUOUS` |
| checkpoint schema desconhecido | `PASS`: `CORRUPTED` |
| checkpoint corrompido | `PASS`: `CORRUPTED` |
| audit event com secret | `PASS`: redigido antes da persistência |

## 9. Total de testes

`37` testes passaram: 6 da Missão 001, 14 da Missão 002 e 17 da Missão 003. O Crash Lab inclui
subprocessos reais próprios e não mata processos do sistema.

## 10. Regressões, bugs e correções

- A adição de `journal_entry` fez uma expectativa legada de 12 schemas falhar; atualizada para 13
  schemas (12 de domínio + journal), sem alterar os contratos existentes.
- `os.kill(pid, 0)` mostrou-se insuficiente para stale detection no Windows; substituído por
  `OpenProcess/GetExitCodeProcess` e coberto por subprocesso real.
- O primeiro teste de lock deixou pipes do subprocesso abertos; stdout/stderr agora são fechados
  explicitamente no Crash Lab.

## 11. Limitações

- JSONL não tem rotação/compactação/retention nem journal transacional de filesystem.
- `FileLock` protege processos no mesmo host; não é lock distribuído.
- Recovery não executa reparo, restauração de backup ou decisão de retry.
- Um registro JSONL final semanticamente inválido não é tolerado; somente truncamento/decodificação
  final é recuperável.
- Não há persistência durável do registry de idempotência fora do journal.
- Não foi simulada falha de energia física nem corrupção de hardware.
- Pause/resume está preparado por campos e estados, mas o Resource Manager ainda não existe.

## 12. Arquivos principais

- `src/localcoder/checkpoints/store.py`
- `src/localcoder/audit/store.py`
- `src/localcoder/mission_engine/journal.py`
- `src/localcoder/persistence/locking.py`
- `src/localcoder/persistence/jsonl.py`
- `src/localcoder/recovery/manager.py`
- `tests/test_mission003.py`
- `tests/crash_helpers.py`
- `docs/missions/003-durable-recovery.md`

## 13. AFolha

`PASS`: worktree observado limpo e nenhum arquivo foi modificado por esta missão.

## 14. TopazioAI

`PASS` no estado observado ao início e no gate final da Missão 003: worktree limpo. As alterações
que existiam durante a Missão 002 não foram tocadas, revertidas, commitadas ou incorporadas.

## 15. Git/GitHub

O remoto é `https://github.com/0xTPZ/LocalCoder.git`, público; não foi usado force push. O commit
de implementação desta missão é `5382c08` (`feat: add durable checkpoint recovery`). O commit
documental final será registrado após esta atualização e o push será confirmado no gate final.
Antes do push foram confirmados testes, scanner, diff check, arquivos não rastreados, ausência de
modelos/binários e worktrees externos limpos.

## 16. Próxima missão recomendada

Missão 004: ingestão segura de projeto sem execução automática, com root canônico, limites de
tamanho, exclusões, encoding e proteção contra path traversal/prompt injection. Não iniciar o
agente autônomo.
