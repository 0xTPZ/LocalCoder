# Arquitetura inicial

## Intenção

LocalCoder deve evoluir de um executor local controlado para um agente capaz de reconstruir
contexto, executar missões bounded e retomar trabalho com checkpoints. As Missões 001 e 002
estabelecem fronteiras e estado persistente; não existe ainda um loop autônomo.

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
| `model_backends` | Porta `ModelBackend` e `ModelProfile` | Somente contrato; adapter não implementado |
| `resource_manager` | Snapshot, lease e porta de estados | Contrato; heurísticas NÃO IMPLEMENTADAS |
| `agents` | Contexto e porta de loop | Contrato; loop NÃO IMPLEMENTADO |
| `capabilities` | Enum de capacidades e allowlist deny-by-default | Política em memória |
| `project` | `ProjectSpec` | Modelo mínimo |
| `mission_engine` | `MissionSpec` e porta | Scheduler/runner NÃO IMPLEMENTADO |
| `checkpoints` | Estrutura compatível e `CheckpointRecord` versionável | Store especializado NÃO IMPLEMENTADO |
| `audit` | Evento estruturado, redaction e adapter em memória | Store durável especializado NÃO IMPLEMENTADO |
| `schemas` | JSON Schema v1, registry e validador controlado | PASS na Missão 002 |
| `persistence` | `AtomicJsonStore` com validação, fsync e `os.replace` | PASS na Missão 002 |
| `state` | UTC, IDs estáveis, redaction, checkpoint e idempotência | PASS na Missão 002 |
| `benchmarks` | Convenções documentais | Harness NÃO IMPLEMENTADO |

## Fronteiras

### Backend de modelo

O núcleo conhece apenas capacidades declaradas e geração normalizada. Um backend concreto deverá
ser selecionável por configuração/política, reportar perfil, expor falhas sem vazar segredos e
liberar seus recursos de modo idempotente. Qwen, llama.cpp, APIs ou qualquer outro runtime são
detalhes substituíveis.

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

Não há planner, executor de comandos, sandbox, loop de reparo, scheduler, store especializado de
longa duração para operações/checkpoints/auditoria, Git automation, navegador, SSH, APIs, e-mail,
redes sociais, carregamento de modelo ou coleta de métricas de hardware dentro do LocalCoder. Isso
é intencional e está coberto no roadmap.
