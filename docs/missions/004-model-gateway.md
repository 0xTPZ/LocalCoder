# Missão 004 — Model Gateway e primeiro laboratório real

Data: 2026-10-03. Mantenedor: `0xTPZ`.

## Objetivo

Implementar um backend de modelo substituível, um Model Gateway independente e o primeiro
laboratório de inferência real usando apenas runtime/modelo já existentes fora do repositório.

## Escopo

- auditoria read-only de runtimes, modelos, endpoints e recursos observáveis;
- contrato executável de health, capabilities, contexto, geração, uso e erros;
- adapter HTTP OpenAI-compatible para runtime local;
- gateway com seleção, preflight health, timeout, normalização, redaction e AuditEvents;
- validação determinística de structured output;
- harness de benchmark v0 e testes A–E;
- integração experimental com `llama.cpp b11344` e Qwen3 4B Q4_K_M sem copiar o modelo.

## Fora de escopo

Não há escolha definitiva de modelo, Resource Manager completo, agente autônomo, shell, browser,
SSH, scheduler, edição de projetos, downloads, cópia de modelos ou dependência estrutural de
AFolha/TopazioAI.

## Riscos e controles

- pressão de RAM/VRAM: processo temporário, endpoint loopback e parada após o laboratório;
- prompt/resposta sensíveis: não são persistidos pelo gateway, harness ou auditoria;
- falha de runtime: erros normalizados e timeout sem corromper checkpoint/journal/audit;
- peculiaridade de runtime: confinada ao adapter HTTP e à configuração, não ao núcleo;
- ambiguidade operacional: nenhum retry automático ou ação externa é iniciado.

## Aceite

Backend funcional, gateway funcional, inferência real concluída, caso objetivo de código,
structured output validado, falhas classificadas, métricas registradas quando disponíveis,
testes anteriores preservados, documentação atualizada e Git sincronizado.

## Testes e rollback

A suíte normal permanece independente de modelo. Testes reais são opt-in e o script
`tools/run_model_lab.py` usa configuração explícita. Rollback: reverter os commits da missão;
nenhum modelo ou projeto externo é removido ou alterado.
