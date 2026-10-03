# Handoff operacional

Atualizado em 2026-10-03, Missão 004.

## Estado atual

`PASS` para Model Backend, Model Gateway, adapter HTTP OpenAI-compatible, structured output,
AuditEvents de inferência, Benchmark Harness v0 e laboratório real CPU A–E. `FAIL` técnico
documentado para o caminho Vulkan no host: o runtime respondeu com saída ilegível. `NOT TESTED`
para streaming/TTFT, CPU/GPU/VRAM portáveis, API remota, Resource Manager completo, Model Manager,
agente autônomo, shell, scheduler e edição de projetos.

## Infraestrutura observada

- `llama.cpp 0.5.0-dev`, build `b11344`, commit `ec7630a64`, CPU e Vulkan, em `E:\TopazioAI`.
- Qwen3 4B/8B/14B GGUF e Q3_K_L foram somente inventariados; nenhum modelo foi copiado.
- Qwen3 4B Q4_K_M foi usado como experimento: CPU passou A–E; Vulkan falhou por saída ilegível.
- Nenhum `llama-server` fica ativo após o laboratório; endpoints experimentais 18080/18081 são
  loopback e foram encerrados.
- TopazioAI resource controller, worker, fila e segredo não foram iniciados ou alterados.

## O que existe

- `src/localcoder/model_backends/`: contratos, erros, adapter HTTP, structured output e gateway.
- `src/localcoder/benchmarks/`: `BenchmarkHarness` e snapshot de RAM com `NOT_TESTED` explícito.
- `configs/model-gateway.example.json`: configuração sem credenciais e local-only.
- `tools/run_model_lab.py`: laboratório A–E real, opt-in e sem persistência de prompts/respostas.
- `tests/test_mission004.py`: testes determinísticos com servidor HTTP falso.
- `tests/test_model_integration.py`: integração real opt-in; não entra como dependência da suíte.
- `docs/audits/MISSION-004-REPORT.md`: evidência completa e baseline.

## Comandos de verificação

```powershell
Set-Location E:\LocalCoder
python -m unittest discover -s tests -v
python tools\check_secrets.py
python -m compileall -q src tests tools
git diff --check
git status --short
```

Laboratório real, somente após iniciar explicitamente um runtime local já existente:

```powershell
python tools\run_model_lab.py --config configs\model-gateway.example.json `
  --endpoint http://127.0.0.1:18081 --runtime "llama.cpp b11344 CPU" `
  --output-dir var\benchmarks\mission004-cpu
```

## Limites importantes

- Não baixar, mover ou versionar modelos.
- Não alterar AFolha, TopazioAI ou outros projetos.
- Não ativar Task Scheduler, controller, runtime permanente ou servidor público.
- Não registrar prompts/respostas integrais em audit ou benchmark.
- Nenhuma ação externa é repetida automaticamente após falha ou crash.

## Git e GitHub

O repositório público é https://github.com/0xTPZ/LocalCoder. O commit de implementação da Missão
004 é `2df6ee0` (`feat: add model gateway and inference lab`); a sincronização documental final
segue no histórico imediatamente posterior. Não usar force push. Antes do push devem passar suíte,
scanner, compilação, schemas, diff check, artefatos proibidos e worktrees externos.

## Próxima missão recomendada

Missão 005: ingestão segura de projeto, com root canônico, manifesto, limites, exclusões, encoding
e proteção contra path traversal/prompt injection. Não iniciar nesta missão.
