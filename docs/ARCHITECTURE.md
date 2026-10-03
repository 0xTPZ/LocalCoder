# Arquitetura inicial

## Intenção

LocalCoder deve evoluir de um executor local controlado para um agente capaz de reconstruir
contexto, executar missões bounded e retomar trabalho com checkpoints. As Missões 001–004
estabelecem fronteiras, estado persistente, recuperação fail-safe e uma porta de inferência real;
não existe ainda um loop autônomo.

## Fluxo alvo

```text
PROJECT → ROADMAP → MISSION → TASK → ACTION → VERIFY → CHECKPOINT → NEXT MISSION
                         │          │        │       │
                         ├──────────┴────────┴───────┤
                         │ audit trail + policy gate │
                         └──────── resource manager ┘
```

O fluxo acima é visão de produto, não uma declaração de funcionalidade implementada.

## Componentes e estado

| Área | Fundação criada | Estado nesta missão |
|---|---|---|
| `core` | Tipos de request/result, estados e contratos comuns | PASS |
| `model_backends` | Contrato, adapter HTTP OpenAI-compatible e Model Gateway | PASS experimental local; modelo/runtimes substituíveis |
| `resource_manager` | Snapshot, lease e porta de estados | Contrato; heurísticas NÃO IMPLEMENTADAS |
| `agents` | Contexto e porta de loop | Contrato; loop NÃO IMPLEMENTADO |
| `capabilities` | Enum de capacidades e allowlist deny-by-default | Política em memória |
| `project` | `ProjectSpec` | Modelo mínimo |
| `mission_engine` | `MissionSpec` e porta | Scheduler/runner NÃO IMPLEMENTADO |
| `checkpoints` | Estrutura compatível e `CheckpointRecord` versionável | `CheckpointStore` durável PASS na Missão 003 |
| `audit` | Evento estruturado, redaction e adapter em memória | `AuditStore` JSONL append-only PASS na Missão 003 |
| `schemas` | JSON Schema v1, registry e validador controlado | PASS na Missão 002 |
| `persistence` | `AtomicJsonStore` com validação, fsync e `os.replace` | PASS na Missão 002 |
| `state` | UTC, IDs estáveis, redaction, checkpoint e idempotência | PASS na Missão 002 |
| `recovery` | Journal, Recovery Manager e estados de restart | PASS na Missão 003 |
| `benchmarks` | Convenções documentais | Harness v0 PASS; métricas de hardware parciais |

## Fronteiras

### Backend de modelo

O núcleo conhece apenas capacidades declaradas e geração normalizada. `ModelGateway` seleciona o
backend por configuração, verifica health, aplica timeout, normaliza uso/timing e audita falhas.
`OpenAICompatibleBackend` é o primeiro adapter experimental; endpoint, runtime e modelo são
configuráveis e o padrão exige loopback. Qwen, llama.cpp, APIs ou qualquer outro runtime são
detalhes substituíveis, não dependências do núcleo.

### Laboratório de modelo

`BenchmarkHarness` executa casos bounded sem persistir prompt ou resposta integral. Structured
output é parseado e validado independentemente do runtime. Métricas ausentes permanecem
`NOT_TESTED`; não há inferência de CPU/GPU/VRAM a partir de valores aproximados.

### Resource Manager

O contrato registra observações e transições, sem assumir thresholds. Estados mínimos:
`WORKING`, `PAUSING`, `SLEEPING`, `RESUMING`, `ERROR` e `WAITING`. Uma implementação futura
deverá definir fonte das métricas, histerese, política de prioridade, cancelamento, recuperação e
evidência antes de tomar decisões automáticas.

### Capacidades

Filesystem, execução de processos, rede, navegador, SSH, e-mail e redes sociais são capacidades
separadas. Nenhuma integração é ativada pela enumeração. O padrão é negar até uma política
explícita conceder a capacidade necessária para uma tarefa específica.

### Checkpoints e auditoria

Checkpoint é memória de retomada; audit trail é histórico de decisão/ação. São conceitos distintos.
`CheckpointRecord` formaliza projeto, roadmap, missão, task, action, etapa concluída, pausa,
próxima ação, backend/modelo e capacidades ativas. `AuditEvent` formaliza actor, projeto, missão,
action, resultado, razão, timestamp e correlation ID. O payload passa por redaction antes de ser
exposto por `to_document()` ou armazenado pelo adapter em memória.

### Schemas e compatibilidade

Cada documento persistente tem `schema_version` inteiro. A versão atual é v1. O `SchemaRegistry`
rejeita versão futura desconhecida, versão não suportada, campos obrigatórios ausentes, tipos
inválidos e propriedades desconhecidas. Não há migração silenciosa nesta fase.

### Persistência atômica

`AtomicJsonStore` valida o objeto, cria um temporário no mesmo diretório/volume, escreve UTF-8,
faz flush e `fsync`, e usa `os.replace`. No Windows, a substituição no mesmo volume é a operação
atômica disponível; o diretório não é submetido a uma operação POSIX de `fsync`. Falhas simuladas
antes da troca preservam o último estado válido.

### Checkpoint Store

`CheckpointStore` encapsula todos os acessos a arquivos de checkpoint. `create` é exclusivo,
`replace` exige uma entrada existente, `get`, `enumerate`, `validate` e `active` retornam apenas
documentos validados. Um lock de diretório cobre criação/substituição; temporários abandonados são
reportados e nunca promovidos automaticamente.

### Audit Store e journal

`AuditStore` grava eventos redigidos em JSONL, com sequência monotônica e deduplicação por
`event_id`. `JournalStore` grava `ACTION_PLANNED`, `ACTION_STARTED`, `ACTION_PAUSED`,
`ACTION_COMPLETED` e `ACTION_FAILED`. A ordem é reconstruída por `sequence`. Somente erro de
decodificação no último registro é tolerado; erro de schema, versão desconhecida ou corrupção em
registro anterior bloqueia a confiança no arquivo.

### Locking

`FileLock` usa criação exclusiva (`O_CREAT|O_EXCL`) de um arquivo de metadados no mesmo volume,
com `lock_id`, PID, host e timestamp. Conflito é imediato e não há espera implícita. Um lock
obsoleto não é removido automaticamente: a remoção exige `lock_id` esperado e confirmação via
`OpenProcess/GetExitCodeProcess` no Windows de que o PID não está vivo.

### Recovery Manager

`RecoveryManager.inspect()` somente lê, valida e classifica: `CLEAN`, `RECOVERABLE`, `AMBIGUOUS`,
`CORRUPTED` ou `BLOCKED`. `ACTION_STARTED`/`ACTION_PAUSED` sem evento terminal vira `AMBIGUOUS` e
tem recomendação `STOP_AND_REQUEST_HUMAN_DECISION`; nenhuma ação externa é repetida.

### Idempotência e tempo

IDs operacionais são UUIDv5 determinísticos derivados de um namespace LocalCoder, tipo e partes
canônicas. Uma operação é escopada por `(action_id, idempotency_key)` e não inicia novamente quando
encontrada. Timestamps são UTC internamente e serializados em ISO-8601 com sufixo `Z`.

## Decisões de fundação

- Monólito modular inicialmente, para manter baixo custo operacional e preservar fronteiras.
- Python 3.12 e biblioteca padrão no runtime inicial, para reduzir superfície de dependências.
- Protocolos/portas antes de adapters concretos, para permitir comparação de modelos e runtimes.
- Estado local ignorado pelo Git; somente schemas, fixtures e metadados reproduzíveis devem ser
  versionados.
- Integrações externas futuras devem ser adapters independentes, nunca imports de AFolha ou
  TopazioAI.

## Não implementado

Não há planner, executor de comandos, sandbox, loop de reparo, scheduler, journal transacional de
ações externas, locking distribuído, backup remoto, Git automation, navegador, SSH, APIs remotas,
e-mail, redes sociais, Model Manager, seleção definitiva de modelo ou coleta completa de métricas
de hardware. O runtime desta missão foi um processo externo iniciado explicitamente e não é
gerenciado continuamente pelo LocalCoder.
