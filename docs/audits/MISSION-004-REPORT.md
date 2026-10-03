# Relatório final — Missão 004

Data: 2026-10-03. Mantenedor: `0xTPZ`.

## 1. Status geral

`PASS` para o Model Backend, Model Gateway, integração local controlada, laboratório CPU real,
falhas, auditoria, métricas disponíveis e documentação. O backend Vulkan foi executado como
experimento e recebeu `FAIL` técnico por resposta ilegível; o resultado não foi ocultado nem
promovido a baseline. Não houve cópia de modelo, alteração de AFolha/TopazioAI, shell autônomo,
scheduler ou agente autônomo.

## 2. Baseline confirmada

Baseline inicial da missão: `b3e9487`. O worktree do LocalCoder estava limpo e `HEAD` coincidiu
com `origin/main` antes do trabalho.

## 3. Infraestrutura descoberta — auditoria read-only

| Item | Observação | Resultado |
|---|---|---|
| Sistema | Windows 10 Enterprise 22H2, build 19045, x64 | PASS |
| Hardware | Intel i7-4790, aproximadamente 16 GiB RAM, AMD RX 580 2048SP | PASS |
| Runtime | `llama.cpp 0.5.0-dev`, build `b11344`, commit `ec7630a64` | PASS |
| Binários | Variantes CPU e Vulkan existentes em `E:\TopazioAI\runtime\...\b11344` | PASS |
| Ollama/LM Studio/vLLM | não encontrados no PATH/estado auditado | NOT TESTED |
| Listeners de inferência | 18080/18081/18150 não tinham listener ao final; `127.0.0.1:18083` pertencia a worker TopazioAI externo observado no gate | PASS local; externo preservado |
| Controller TopazioAI | configuração e scripts estudados somente por leitura; não iniciado | PASS |
| AFolha | consumidor documentado separado; nenhum endpoint/job foi acessado | PASS |

Modelos GGUF existentes, observados fora do repositório e não copiados:

| Modelo/quantização | Tamanho observado | Uso nesta missão |
|---|---:|---|
| Qwen3 4B Q4_K_M | 2.497.280.256 bytes | baseline real CPU; Vulkan experimental |
| Qwen3 8B Q4_K_M | 5.027.783.488 bytes | somente inventário |
| Qwen3 14B Q4_K_M | 9.001.752.960 bytes | somente inventário |
| Qwen3 14B Q3_K_L | 7.900.651.552 bytes | somente inventário |

Configuração real usada: Qwen3 4B Q4_K_M, contexto 2048, `-ngl 0` no CPU, `-ngl 99` no Vulkan,
`--reasoning off`, bind exclusivo em loopback. O caminho do modelo permaneceu em `E:\TopazioAI`;
o LocalCoder só enviou requisições HTTP ao runtime.

## 4. Arquitetura implementada

```text
GatewayConfig → ModelGateway → ModelBackend contract
                              └→ OpenAICompatibleBackend → HTTP loopback runtime externo
                                                              └→ modelo existente
                                      ↓
                      health / timeout / normalized result / metrics
                                      ↓
                    redacted AuditEvents + BenchmarkResult v1
```

O núcleo não conhece llama.cpp, Qwen, caminhos de modelo, scripts privados ou filas de outros
projetos. O adapter aceita endpoint, runtime, modelo, contexto, timeout e parâmetros por
configuração. `local_only=true` exige endpoint loopback e credenciais nunca são lidas para logs.

## 5. Model Backend e Gateway

- `BackendHealth`, `BackendCapabilities`, `GenerationRequest` e `GenerationResult` ampliam a
  porta existente sem acoplar o restante do sistema ao protocolo HTTP.
- `OpenAICompatibleBackend` normaliza `/health` e `/v1/chat/completions`, usage, timings,
  finish reason e falhas de transporte/resposta.
- `ModelGateway` seleciona o backend configurado, executa preflight health, aplica timeout,
  valida structured output e produz `MODEL_HEALTH_CHECKED`, `MODEL_GENERATION_STARTED`,
  `MODEL_GENERATION_COMPLETED` e `MODEL_GENERATION_FAILED`.
- AuditEvents armazenam somente metadados e métricas sanitizados. Prompt e resposta integral não
  são persistidos.
- O `BenchmarkHarness` registra latency, tokens, tokens/s quando o runtime informa, RAM antes/depois
  e marca CPU, GPU, VRAM e TTFT como `NOT_TESTED` quando não há medição confiável.

## 6. Testes A–E — baseline CPU

| Teste | Verificação objetiva | Resultado |
|---|---|---|
| A — instrução simples | token `LOCALCODER_OK` observado | PASS |
| B — código | resultado objetivo de `2 + 3` contém inteiro `5` | PASS |
| C — structured output | JSON exato `{language: python, answer: 5, passed: true}` validado pelo schema | PASS |
| D — contexto | codinome fornecido `amber-otter-417` recuperado | PASS |
| E — erro | endpoint loopback inexistente classificado `BACKEND_UNAVAILABLE` | PASS |

## 7. MODEL LAB BASELINE

Runtime: `llama.cpp b11344 CPU`; modelo: Qwen3 4B Q4_K_M; quantização: Q4_K_M; contexto: 2048;
temperatura: 0,0; `top_p=0,8`; `top_k=20`; `min_p=0,0`; bind: `127.0.0.1:18081`.

| Caso | Latência | Prompt tokens | Generated tokens | Tokens/s | RAM disponível antes/depois |
|---|---:|---:|---:|---:|---:|
| A | 1.274 ms | 24 | 5 | 7,142 | 3,868 / 4,035 GiB |
| B | 4.295 ms | 31 | 26 | 7,141 | 4,035 / 4,376 GiB |
| C | 4.302 ms | 47 | 23 | 7,018 | 4,376 / 4,361 GiB |
| D | 2.320 ms | 45 | 9 | 7,046 | 4,361 / 4,353 GiB |

O processo CPU observado no health tinha aproximadamente 4,31 GiB de working set; a medição é
instantânea e não deve ser tratada como pico completo. TTFT, CPU%, GPU% e VRAM são `NOT TESTED`
no harness. Os tokens/s acima são métricas do runtime quando disponíveis; não são extrapolação.

## 8. Experimento Vulkan

`llama.cpp b11344 Vulkan` carregou e respondeu em `127.0.0.1:18080`, mas o conteúdo retornado
foi ilegível/repetitivo, com Unicode/tokens incompatíveis, em quatro chamadas. A resposta não foi
aceita como geração válida; A–D ficaram `FAIL`. E continuou `PASS`. O servidor foi encerrado e o
resultado foi mantido como falha de compatibilidade/qualidade do caminho Vulkan neste host, não
como falha do contrato do gateway.

Durante o gate final foi observado um worker externo do TopazioAI em `127.0.0.1:18083`, com
Qwen3 8B Vulkan, `-ngl 36`, contexto 2048 e `-Once`. A linha de comando identifica
`E:\TopazioAI\scripts\topazio-ai-worker.ps1`; o LocalCoder não iniciou, parou, consultou a fila
ou alterou esse processo. Ele foi preservado para não interromper outro consumidor.

## 9. Falhas e recuperação

| Falha | Resultado |
|---|---|
| endpoint inexistente | PASS — `BACKEND_UNAVAILABLE`, retryable |
| timeout | PASS — `BACKEND_TIMEOUT` |
| JSON/resposta inválida | PASS — `INVALID_BACKEND_RESPONSE` |
| backend HTTP 503 | PASS — health `UNAVAILABLE`, gateway fail-closed |
| modelo não configurado | PASS — `MODEL_UNAVAILABLE` |
| structured output inválido | PASS — `STRUCTURED_OUTPUT_INVALID` |
| erro de inferência | PASS — não altera checkpoint/journal/audit de estado anterior |
| interrupção física/power loss | NOT TESTED |

## 10. Testes automatizados

`45` testes foram coletados: `44` passaram e `1` integração real foi marcada `skipped` por ser
opt-in na suíte normal. Os 37 testes das Missões 001–003 continuam passando; `tests/test_mission004.py`
adiciona adapter, gateway, structured output, erros e harness; `tools/run_model_lab.py` executou
o laboratório real A–E com resultado CPU `PASS`.

## 11. Segurança e política de dados

- Nenhuma credencial foi colocada na configuração de exemplo ou no Git.
- Endpoint remoto é rejeitado por padrão (`local_only=true`); o experimento usou loopback.
- Prompt e resposta não entram em AuditStore nem BenchmarkResult.
- Redaction continua aplicada a erros, metadados e métricas.
- Não houve import, execução, escrita, fila, job, download ou cópia em AFolha/TopazioAI.
- O processo externo iniciado pelo LocalCoder foi encerrado; os ports 18080/18081 ficaram livres.
  O worker TopazioAI em 18083 foi observado e preservado, sem intervenção do LocalCoder.

## 12. Limitações

- Não há streaming; TTFT permanece `NOT TESTED`.
- CPU/GPU/VRAM não têm fonte portátil confiável no harness; ficam `NOT TESTED`.
- Não há Model Manager, unload automático, Resource Manager completo ou lock distribuído.
- Não há API remota, múltiplos backends em produção, retry automático ou seleção definitiva de modelo.
- A saída Vulkan foi reprovada no host; nenhuma conclusão de qualidade foi extrapolada para outros
  modelos ou máquinas.
- A medição de RAM é amostragem antes/depois, não perfil completo de pico.

## 13. AFolha

`PASS`: worktree permaneceu limpo e nenhum comando da missão escreveu no projeto.

## 14. TopazioAI

`PASS`: worktree permaneceu limpo; runtime e modelos foram somente lidos. O laboratório do
LocalCoder não executou scripts do controller nem tocou fila, segredo, configuração ou arquivo do
projeto. Um worker TopazioAI externo foi observado em execução e preservado.

## 15. Git/GitHub

O repositório público `0xTPZ/LocalCoder` foi atualizado sem force push. `2df6ee0` (`feat: add model
gateway and inference lab`) contém a implementação; `bfd281f` (`docs: finalize Mission 004 evidence`)
contém a evidência documental publicada. O gate final inclui testes, scanner, compilação, schemas,
diff check, artefatos proibidos e worktrees externos.

## 16. Próxima missão recomendada

Missão 005: ingestão segura de projeto, com root canônico, manifesto, limites de tamanho,
exclusões, encoding e proteção contra path traversal/prompt injection. Não iniciar nesta missão.
