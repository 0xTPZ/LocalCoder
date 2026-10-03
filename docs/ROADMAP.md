# Roadmap

Este roadmap transforma a visão inicial em missões verificáveis. Ele não autoriza avanço
automático: cada missão deve ser aprovada/selecionada e terminar com evidência.

## Fase 0 — Fundação e inventário

### Missão 001 — concluída nesta entrega

- **Objetivo:** criar a raiz, registrar o ambiente, separar fronteiras e estabelecer documentação
  operacional.
- **Contexto:** não existia repositório LocalCoder; havia infraestrutura local compartilhada que
  não poderia ser copiada nem alterada.
- **Escopo:** auditoria read-only, contratos, estrutura Python, Git, segurança documental e
  relatório.
- **Fora de escopo:** agente completo, inferência, downloads, heurísticas de recursos,
  integração produtiva, mudanças externas.
- **Aceite:** estrutura reproduzível, testes da fundação, scanner de segredos, diff revisado,
  Git inicial e documentação coerente.
- **Rollback:** remover o commit local de fundação ou arquivar a raiz `E:\LocalCoder`; não há
  alterações necessárias em outros projetos.

## Fase 1 — Contratos executáveis e estado local seguro

### Missão 002 — especificar antes de implementar

- **Objetivo:** definir schemas versionados de projeto, roadmap, missão, ação, resultado,
  checkpoint e evento de auditoria.
- **Riscos:** schema rígido demais para evolução; persistência de dados sensíveis.
- **Tarefas:** escrever schemas, política de compatibilidade, redaction, IDs/idempotência e
  casos de erro.
- **Aceite:** validação determinística, fixtures válidas/ inválidas, migração documentada,
  nenhum segredo nos fixtures.
- **Testes:** unitários, propriedades de idempotência, casos de schema incompatível.
- **Rollback:** manter versão anterior de schema e rejeitar novas versões desconhecidas.

### Missão 003 — checkpoint e audit trail duráveis

- **Objetivo:** persistir retomada e trilha de decisão sem perder atomicidade.
- **Riscos:** corrupção, duplicidade, exposição de contexto, corrida entre processos.
- **Tarefas:** store transacional local, locking, recuperação após crash, retenção e exportação.
- **Aceite:** crash injection, replay sem duplicidade, hash/identidade dos eventos, backup e
  restauração documentados.
- **Testes:** concorrência controlada, interrupção em cada etapa, scanner de dados sensíveis.
- **Rollback:** leitura compatível da versão anterior e restauração de backup testado.

## Fase 2 — Projeto, roadmap e missão bounded

### Missão 004 — ingestão segura de projeto

- **Objetivo:** registrar um projeto e seu roadmap sem executar conteúdo automaticamente.
- **Riscos:** path traversal, links maliciosos, prompt injection em documentação do projeto,
  escopo de filesystem.
- **Aceite:** root canônico, manifesto, limites de tamanho, exclusões e relatório de inventário.
- **Testes:** caminhos inválidos, symlinks/junctions, arquivos grandes, encoding e crash.
- **Rollback:** apagar somente o estado derivado do projeto, preservando fonte externa.

### Missão 005 — motor de missões com pausa/retomada

- **Objetivo:** executar uma tarefa bounded, verificar resultado e salvar checkpoint.
- **Riscos:** loops, ações irreversíveis, estado parcial, reexecução.
- **Aceite:** limite de passos/tempo/tentativas, pausa explícita, retomada exata, fail-closed.
- **Testes:** falha em cada transição, repetição, cancelamento e recuperação.
- **Rollback:** reverter checkpoint e artefatos gerados, nunca presumir que comando externo é
  reversível.

## Fase 3 — capacidades controladas

### Missão 006 — ferramenta de leitura e análise

- **Objetivo:** permitir somente leitura delimitada e registrar cada acesso.
- **Fora de escopo:** escrita e execução de processos.
- **Aceite:** allowlist de root, limites, redaction, audit trail e testes de evasão.

### Missão 007 — escrita com patch e rollback

- **Objetivo:** editar arquivos com diff, backup e validação antes/depois.
- **Riscos:** sobrescrita, arquivos fora do projeto, segredos, corrupção de encoding.
- **Aceite:** dry-run, diff obrigatório, confirmação de política, rollback testado.

### Missão 008 — execução de comandos sandboxed

- **Objetivo:** executar comandos explicitamente permitidos com timeout e captura segura.
- **Fora de escopo:** privilégios elevados e comandos administrativos.
- **Aceite:** allowlist, ambiente sanitizado, limite de CPU/RAM/tempo, kill e logs sem segredos.

## Fase 4 — backend de modelo e recuperação

### Missão 009 — adapter de modelo substituível

- **Objetivo:** implementar um backend experimental atrás da porta existente.
- **Aceite:** health, timeout, cancelamento, métricas, erro normalizado, shutdown e fixture fake.
- **Regra:** nenhum modelo será escolhido como definitivo por antecipação.

### Missão 010 — planner/verifier/retry bounded

- **Objetivo:** planejar ações, verificar evidência e corrigir com limites.
- **Riscos:** alucinação, loops, deriva de objetivo e custo de recursos.
- **Aceite:** critérios objetivos, no máximo N tentativas, checkpoint por etapa, auditoria e
  parada humana em risco.

## Fase 5 — Resource Manager

### Missão 011 — observação sem decisão

- **Objetivo:** coletar RAM/CPU/VRAM/processos de forma portable e somente local.
- **Aceite:** fonte, precisão, indisponibilidade e custo documentados.

### Missão 012 — política de pausa e retomada

- **Objetivo:** aplicar política baseada em evidência e prioridade.
- **Aceite:** estados completos, histerese, sleep/resume, liberação de recursos, crash recovery e
  testes sem modelo.
- **Bloqueio:** não adotar thresholds vindos de outro projeto sem validação específica.

## Fase 6 — operação e comparação

### Missão 013 — benchmark harness

- **Objetivo:** comparar qualidade, raciocínio, ferramentas, recuperação, velocidade, RAM/VRAM,
  contexto e estabilidade sob condições registradas.
- **Aceite:** fixtures, protocolo, resultados reproduzíveis e licença/proveniência.

### Missão 014 — operação contínua segura

- **Objetivo:** scheduler, checkpoints de longo prazo, handoff, logs rotativos e observabilidade.
- **Aceite:** crash/reboot, pausa por uso do computador, retomada e operação sem exposição de
  segredos.

## Template obrigatório de missão

Cada nova missão deve conter: objetivo, contexto, escopo, fora de escopo, riscos, tarefas,
critérios de aceite objetivos, testes, documentação necessária, rollback, evidências e decisão
de encerramento (`PASS`, `FAIL`, `BLOCKED` ou `NOT TESTED`).
