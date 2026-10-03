# LocalCoder

LocalCoder é um projeto open source em fundação para um agente local autônomo orientado a
projetos, roadmaps e missões. O mantenedor público é **0xTPZ**.

Esta primeira entrega é a Missão 001: inventário técnico, arquitetura inicial, contratos de
fronteira e documentação operacional. Ela não implementa um agente completo, não baixa modelos,
não executa comandos de projetos externos e não ativa automação contínua.

## Estado da fundação

- Pacote Python 3.12 sem dependências de runtime obrigatórias.
- Contratos separados para backends de modelo, recursos, capacidades, projetos, missões,
  checkpoints e auditoria.
- Estados de Resource Manager previstos: `WORKING`, `PAUSING`, `SLEEPING`, `RESUMING`,
  `ERROR` e `WAITING`.
- Backend de modelo substituível; nenhum modelo é requisito do núcleo.
- Dados locais, logs e checkpoints ignorados pelo Git.
- Testes determinísticos da fundação e scanner heurístico de segredos.

## Começar

No PowerShell:

```powershell
Set-Location E:\LocalCoder
python -m unittest discover -s tests -v
python tools\check_secrets.py
python -m localcoder
```

Para usar o pacote como instalação editável em um ambiente isolado:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
```

Nenhum comando de desenvolvimento baixa modelos ou altera `E:\AFolha`, `E:\TopazioAI` ou outro
projeto. A instalação editável modifica somente o ambiente virtual local, que é ignorado pelo Git.

## Documentação

- [Arquitetura](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Decisões](docs/DECISIONS.md)
- [Segurança](docs/SECURITY.md)
- [Desenvolvimento](docs/DEVELOPMENT.md)
- [Constituição operacional](AGENTS.md)
- [Handoff](docs/HANDOFF.md)
- [Relatório da Missão 001](docs/audits/MISSION-001-REPORT.md)

## Licença

A licença open source ainda requer decisão humana e, por isso, não foi inventada nesta missão.
Consulte `docs/DECISIONS.md` antes de publicar um arquivo `LICENSE`.
