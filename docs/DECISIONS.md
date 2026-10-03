# Registro de decisões

## ADR-001 — Fundação independente em Python

- **Status:** vigente.
- **Decisão:** usar Python 3.12, biblioteca padrão no runtime inicial e um monólito modular.
- **Motivo:** reduz dependências e permite desenvolver contratos antes de escolher runtime/modelo.
- **Consequência:** adapters e persistência ainda precisam ser construídos.
- **Alternativas rejeitadas:** copiar estrutura interna de AFolha/TopazioAI; acoplar ao Node;
  escolher um modelo definitivo.

## ADR-002 — Modelo como backend substituível

- **Status:** vigente.
- **Decisão:** o núcleo conhece `ModelBackend`, `ModelProfile`, request e result normalizados.
- **Motivo:** a missão exige comparar modelos por qualidade, custo computacional, estabilidade
  e uso de ferramentas.
- **Consequência:** capacidades específicas devem ser declaradas, não presumidas.

## ADR-003 — Resource Manager sem heurística nesta missão

- **Status:** vigente.
- **Decisão:** registrar estados e portas, sem thresholds ou decisões automáticas.
- **Motivo:** o pedido exige estudar o ambiente antes de implementar heurísticas arbitrárias.
- **Evidência ambiental:** hardware e estado do controlador existente foram inventariados no
  relatório da Missão 001, mas não são política do LocalCoder.

## ADR-004 — Referência técnica sem dependência estrutural

- **Status:** vigente.
- **Decisão:** reutilizar conceitos documentados de contratos, filas, estado `UNLOADED`,
  validação, idempotência e resource-awareness; reimplementar no LocalCoder quando necessário.
- **Motivo:** AFolha e TopazioAI têm consumidores e ciclos de vida próprios.
- **Consequência:** qualquer futura integração deve ocorrer por adapter/contrato versionado.

## ADR-005 — Capacidades deny-by-default

- **Status:** vigente.
- **Decisão:** filesystem write, execução de processos, rede, navegador, SSH, e-mail e redes
  sociais começam negados e separados.
- **Motivo:** autonomia não deve significar irreversibilidade ou expansão silenciosa de acesso.

## ADR-006 — Apache License 2.0

- **Status:** vigente.
- **Decisão:** distribuir o LocalCoder sob Apache License 2.0, com o texto oficial em `LICENSE`.
- **Motivo:** decisão explícita da Missão 002, com licença permissiva e concessão de patentes.

## ADR-007 — Versionamento explícito de documentos

- **Status:** vigente.
- **Decisão:** todo documento persistente possui `schema_version` inteiro no objeto raiz; v1 é a
  única versão suportada. O registry rejeita versões futuras e versões não suportadas.
- **Motivo:** evitar interpretação silenciosa de estado incompatível e permitir migrações futuras
  deliberadas.

## ADR-008 — Persistência JSON atômica no mesmo volume

- **Status:** vigente.
- **Decisão:** validar antes de gravar, escrever temporário no mesmo diretório, `flush`/`fsync` e
  `os.replace`; falha antes da troca não altera o último estado válido.
- **Motivo:** o alvo inicial é Windows e a interrupção durante escrita não pode destruir o estado.
- **Limitação:** não há `fsync` de diretório POSIX no caminho Windows; crash recovery completo
  permanece missão posterior.

## ADR-009 — UUIDv5 determinístico e UTC

- **Status:** vigente.
- **Decisão:** IDs estáveis usam UUIDv5 com namespace LocalCoder e partes canônicas; timestamps
  usam UTC interno e ISO-8601 com `Z` na persistência.
- **Motivo:** repetição deve reencontrar a mesma operação, sem depender de nome humano ou relógio
  local para identidade.

## ADR-010 — Redaction centralizada e fail-safe

- **Status:** vigente.
- **Decisão:** logs/auditoria/resultados passam por redaction baseada em chaves sensíveis e padrões
  de alto sinal, com `[REDACTED]`; o detector é pequeno e extensível, não universal.
- **Motivo:** reduzir vazamento acidental sem registrar segredos reais nos testes.

## ADR-011 — JSONL append-only para audit e journal

- **Status:** vigente.
- **Decisão:** usar um registro JSON por linha, sequência monotônica e `fsync` após cada append.
- **Motivo:** facilita reconstrução ordenada e permite tolerar somente o último registro truncado,
  mantendo corrupção anterior visível.
- **Consequência:** compactação, retenção e rotação ficam para missão posterior.

## ADR-012 — Lock exclusivo sem remoção automática de stale

- **Status:** vigente.
- **Decisão:** criar lock por `O_EXCL`, registrar PID/host/lock_id e falhar imediatamente em
  conflito. No Windows, consultar `GetExitCodeProcess`; stale só pode ser removido explicitamente
  com lock_id correspondente e PID morto.
- **Motivo:** evitar que uma instância sobrescreva estado de outra e evitar remoção agressiva após
  PID reuse ou falha de leitura.

## ADR-013 — Recovery fail-safe e ambiguidade humana

- **Status:** vigente.
- **Decisão:** `ACTION_STARTED` sem `ACTION_COMPLETED`/`ACTION_FAILED` classifica `AMBIGUOUS` e
  nunca repete automaticamente. Recovery somente inspeciona e produz decisão/evidência.
- **Motivo:** uma ação futura poderá publicar, executar comando ou chamar API; repetir pode ser
  irreversível.

## ADR-014 — Gateway central e adapter HTTP substituível

- **Status:** vigente experimental.
- **Decisão:** o núcleo chama `ModelGateway`; o primeiro adapter concreto fala HTTP
  OpenAI-compatible com endpoint configurado. O padrão aceita somente loopback.
- **Motivo:** provar inferência real sem importar código, modelo, fila ou runtime de AFolha/TopazioAI.
- **Consequência:** peculiaridades de llama.cpp ficam no adapter/configuração; múltiplos backends,
  streaming e API remota ficam para missão futura.

## ADR-015 — Baseline CPU antes de promover Vulkan

- **Status:** vigente para a baseline da Missão 004.
- **Decisão:** usar Qwen3 4B Q4_K_M em `llama.cpp b11344 CPU` como baseline reproduzível; manter
  Vulkan somente como experimento até resolver a saída ilegível observada.
- **Motivo:** o mesmo modelo passou A–E no CPU, enquanto o caminho Vulkan respondeu com conteúdo
  ilegível no host. Não extrapolar qualidade ou estabilidade entre backends.
- **Consequência:** nenhum modelo é definitivo e as métricas CPU não são comparáveis diretamente
  com Vulkan.
