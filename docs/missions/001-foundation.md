# Missão 001 — Fundação, inventário técnico e arquitetura inicial

## Objetivo

Estabelecer uma base independente, rastreável e segura para o LocalCoder, depois de uma auditoria
read-only do ambiente local.

## Contexto

O ambiente possui AFolha e TopazioAI com infraestrutura de modelos e resource-awareness. Esses
projetos têm regras próprias e consumidores adicionais; a missão proíbe mudanças neles e cópia
estrutural sem adaptação independente.

## Escopo

- Inventário de hardware, Windows, linguagens, Git/GitHub CLI, runtimes, servidores, modelos e
  ferramentas.
- Pesquisa conceitual de AFolha/TopazioAI.
- Estrutura Python modular e contratos.
- Git e documentação operacional.
- Validação local e relatório.

## Fora de escopo

Inferência, download de modelo, agente completo, execução de comandos, scheduler, heurísticas de
recursos, integração de produção, navegador, SSH, APIs, e-mail, redes sociais e alterações nos
projetos existentes.

## Critérios de aceite

- [x] Inventário não destrutivo registrado.
- [x] Reutilizar/adaptar/reimplementar/não utilizar diferenciado.
- [x] Árvore inicial criada em `E:\LocalCoder`.
- [x] Documentação mínima e constituição criadas.
- [x] Testes e scanner executados.
- [x] Diff, `.gitignore`, Git e situação do GitHub verificados.
- [x] Limitações e decisões humanas pendentes registradas.

## Evidências

Ver `docs/audits/MISSION-001-INVENTORY.md` e `docs/audits/MISSION-001-REPORT.md`.
