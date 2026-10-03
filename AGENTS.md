# Constituição operacional do LocalCoder

Este documento é obrigatório para qualquer agente, automação ou desenvolvedor que trabalhe no
repositório.

## Escopo e autoria

- A raiz oficial é `E:\LocalCoder`.
- O mantenedor público e a autoria a serem mencionados são `0xTPZ`.
- Não modificar outros projetos para atender ao LocalCoder.
- `E:\AFolha` e `E:\TopazioAI` podem ser estudados como referências técnicas, mas o núcleo do
  LocalCoder não pode importar código privado, banco, prompts, credenciais ou estado deles.

## Modo de missão

Cada missão deve declarar objetivo, contexto, escopo, fora de escopo, riscos, tarefas, aceite,
testes, documentação e rollback. Trabalhos autônomos devem terminar com evidência, não com
suposições.

Use exclusivamente estes resultados:

- `PASS`: há evidência reproduzível;
- `FAIL`: a verificação foi executada e falhou;
- `BLOCKED`: não foi possível avançar por uma dependência externa ou decisão necessária;
- `NOT TESTED`: a verificação ainda não foi executada.

## Segurança e reversibilidade

- Nunca versionar segredos, tokens, senhas, cookies, chaves, dumps privados ou modelos grandes.
- Preferir operações idempotentes e reversíveis.
- Toda mudança autônoma deve ser auditável e possuir caminho de rollback.
- Não iniciar processos externos, rede, navegador, SSH ou administração de serviços sem uma
  capacidade explicitamente autorizada.
- Não esconder um erro corrigido: registrar problema, causa, investigação, solução, validação e
  lição quando relevante.

## Dependências e modelos

- O backend de modelo é substituível; não acoplar o núcleo a Qwen, llama.cpp, TopazioAI ou um
  fornecedor específico.
- Não baixar modelos automaticamente.
- O Resource Manager deve ser baseado em observações e políticas explícitas. Não inserir
  thresholds ou heurísticas arbitrárias sem decisão registrada e estudo do ambiente.
- Integrações futuras com TopazioAI devem usar contratos documentados, nunca imports de arquivos
  privados.

## Git e qualidade

Antes de cada commit:

1. executar testes relevantes;
2. executar o scanner de segredos;
3. conferir `git diff --check`;
4. examinar o diff completo;
5. confirmar que só há arquivos pertencentes ao LocalCoder;
6. registrar decisões e limitações.

Não usar force push, não reescrever histórico remoto e não marcar algo como implementado porque
parece correto.

## Handoff

`docs/HANDOFF.md` deve sempre informar o estado real, comandos de validação, falhas, pendências,
Git, remoto e a próxima missão exata. Outro agente deve conseguir continuar sem acesso à conversa.
