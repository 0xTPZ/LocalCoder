# Handoff operacional

Atualizado em 2026-10-06, Missão de consolidação e preservação.

## Estado atual

`PASS` para Model Backend, Model Gateway, adapter HTTP OpenAI-compatible, structured output,
AuditEvents de inferência, Benchmark Harness v0 e laboratório real CPU A–E. `FAIL` técnico
documentado para o caminho Vulkan no host: o runtime respondeu com saída ilegível. `NOT TESTED`
para streaming/TTFT, CPU/GPU/VRAM portáveis, API remota, Resource Manager completo, Model Manager,
agente autônomo, shell, scheduler e edição de projetos.

A auditoria completa do PC também está `PASS`: não foi encontrada uma segunda árvore de código,
nenhum item exclusivo ficou fora de `E:\LocalCoder` e a árvore local e o GitHub estão alinhados.
Nenhum comando da missão escreveu em projeto externo. `TopazioAI` permaneceu limpo; `AFolha`
apresentou alterações externas durante a janela final e foi preservado sem intervenção. Evidência:
`docs/audits/FULL-PC-LOCALCODER-CONSOLIDATION.md`.

## Infraestrutura observada

- `llama.cpp 0.5.0-dev`, build `b11344`, commit `ec7630a64`, CPU e Vulkan, em `E:\TopazioAI`.
- Qwen3 4B/8B/14B GGUF e Q3_K_L foram somente inventariados; nenhum modelo foi copiado.
- Qwen3 4B Q4_K_M foi usado como experimento: CPU passou A–E; Vulkan falhou por saída ilegível.
- Nenhum processo/listener do laboratório LocalCoder fica ativo; endpoints experimentais 18080/18081
  foram encerrados. Um worker TopazioAI externo pode permanecer em 18083 e não deve ser interrompido.
- TopazioAI resource controller, fila e segredo não foram iniciados pelo LocalCoder nem alterados;
  um worker externo foi observado em 18083 e preservado.

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

O repositório público é https://github.com/0xTPZ/LocalCoder. Os commits anteriores incluem `2df6ee0`
(`feat: add model gateway and inference lab`), `bfd281f` (`docs: finalize Mission 004 evidence`) e
`a8fcf00` (`docs: record external runtime preservation`). A consolidação foi registrada em commits
adicionais desta missão; o fechamento exige `HEAD == origin/main`, working tree limpo e sem force
push. O worker externo observado em 18083 deve ser preservado; o gate local considera apenas os
processos/ports iniciados pelo laboratório.

## Próxima missão recomendada

Missão 005: ingestão segura de projeto, com root canônico, manifesto, limites, exclusões, encoding
e proteção contra path traversal/prompt injection. Não iniciar nesta missão.
