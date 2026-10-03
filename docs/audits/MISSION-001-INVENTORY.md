# Inventário técnico — Missão 001

Data da coleta: 2026-10-03, horário local de São Paulo. A coleta foi read-only. Caminhos e
valores sensíveis foram deliberadamente omitidos.

## Hardware e sistema

| Item | Observação | Resultado |
|---|---|---|
| Sistema | Windows 10 Enterprise, build 19045, 64-bit | PASS |
| Host | `ANIMX-PC` | PASS |
| CPU | Intel Core i7-4790, 4 cores / 8 threads, 3.601 MHz | PASS |
| Memória física | Aproximadamente 15,92 GiB visíveis; coleta observou aproximadamente 9,21 GiB livres | PASS |
| GPU | AMD Radeon RX 580 2048SP e Intel HD Graphics 4600 | PASS |
| Driver AMD | `31.0.21001.14018` | PASS |
| VRAM WMI | Capacidade não retornada de forma confiável pela consulta usada | NOT TESTED |
| Disco E: | Aproximadamente 825,83 GiB livres | PASS |

O valor de VRAM não foi inventado. A documentação do TopazioAI registra uma configuração
experimental de RX 580, mas isso não é tratado como medição independente do LocalCoder.

## Ferramentas

| Ferramenta | Resultado observado |
|---|---|
| Python | 3.12.10 em `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe` |
| Node.js | v24.19.0 |
| npm | 11.17.0 |
| Git | 2.55.0.windows.3 |
| GitHub CLI | 2.101.0; autenticado como `0xTPZ`, protocolo HTTPS |
| ripgrep | 15.2.0 |
| pytest | 9.1.1 |
| CMake | disponível |
| Cargo/Rust | disponíveis |
| .NET | disponível |
| uv/conda/docker/podman | não encontrados no PATH |
| Ollama/LM Studio/nvidia-smi | não encontrados no PATH |
| WSL | Ubuntu 24.04, Zelvya-Dev e Alice-DB-Test registrados; dois ambientes em execução |

## Runtimes, servidores e modelos

- Não foram encontrados listeners nas portas locais comuns consultadas: 11434, 1234, 8000,
  8080, 3000, 5000, 7860 e 9000.
- Não havia processo de Ollama/LM Studio/llama-server/vLLM identificado na consulta.
- Não existe `.ollama`, LM Studio ou diretório genérico de modelos nos caminhos examinados.
- O cache Hugging Face local existe, com 9 arquivos e aproximadamente 0,31 GiB; nenhum modelo
  foi baixado nesta missão.
- `E:\TopazioAI` contém aproximadamente 22,93 GiB e os seguintes GGUF:
  - Qwen3 4B Q4_K_M: aproximadamente 2,33 GiB;
  - Qwen3 8B Q4_K_M: aproximadamente 4,68 GiB;
  - Qwen3 14B Q4_K_M: aproximadamente 8,38 GiB;
  - Qwen3 14B Q3_K_L: aproximadamente 7,36 GiB.
- O TopazioAI documenta `llama.cpp b11344` Vulkan/CPU sob demanda e estado normal
  `MODEL=UNLOADED`. O runtime não foi iniciado.
- A tarefa `TopazioAI.ResourceAwareController` existe e estava `Disabled`.

## AFolha

- Raiz: `E:\AFolha`.
- Git: branch `main`, worktree limpo durante a auditoria, remoto `https://github.com/0xTPZ/afolha.git`.
- O projeto possui contrato `LocalProvider` e documentação de worker privado, HMAC, lease,
  validação, grounding e desligamento seguro.
- O perfil local documentado usa Qwen3 como candidato operacional/benchmark, mas o E2E descrito
  está bloqueado por pressão de memória e a ativação produtiva permanece desligada.
- O AGENTS do AFolha proíbe tocar outros projetos e exige testes/documentação próprios.

## TopazioAI

- Raiz: `E:\TopazioAI`; árvore Git separada e worktree limpo durante a auditoria.
- O registry lista AFolha ativo e LocalCoder planejado como consumidores distintos.
- Contratos compartilhados documentados: Model Manager, Job Runner, job/result schemas e
  validação de resultados.
- O perfil planejado do LocalCoder é local-only, sem structured output obrigatório, com limites
  registrados no perfil do consumidor.
- A infraestrutura tem filas, perfis, schemas, benchmarks, resource controller e documentação.
- O núcleo do LocalCoder não reutiliza arquivos privados; somente conceitos foram utilizados para
  desenhar portas independentes.

## Classificação de reutilização

| Origem/conceito | Classificação LocalCoder | Justificativa |
|---|---|---|
| Contrato de backend/model profile | REIMPLEMENTAR | A ideia é útil; o código dos consumidores não entra no núcleo |
| Job bounded, idempotência, lease e resultado validado | ADAPTAR | Aplicar ao domínio de missões, com schemas próprios |
| `MODEL=UNLOADED` e shutdown explícito | REUTILIZAR CONCEITUALMENTE | Invariante útil para liberar recursos |
| Resource-aware states e observabilidade | ADAPTAR | Coletar dados do próprio ambiente, sem copiar thresholds |
| AFolha DB, queues, prompts, secrets, worker | NÃO UTILIZAR | Pertencem ao consumidor e seriam acoplamento indevido |
| TopazioAI model files/runtime | NÃO COPIAR | Artefatos grandes compartilhados; usar adapter futuro por contrato |
| AFolha/TopazioAI código fonte | NÃO COPIAR | Proteger isolamento e proveniência |

## Limitações da auditoria

- A medição de VRAM pelo WMI não foi confiável.
- Não foram iniciados runtimes nem inferência para provar capacidade real do modelo.
- A auditoria de segredos cobre o repositório LocalCoder; não audita conteúdo de outros projetos.
- Não houve consulta remota ao GitHub além do estado de autenticação e existência do repositório.
