# Auditoria completa de consolidação e preservação

**Data:** 2026-10-06
**Repositório canônico:** `E:\LocalCoder` / `0xTPZ/LocalCoder`
**Resultado da missão:** `PASS`

## Decisão executiva

`E:\LocalCoder` continua sendo a única fonte local oficial do código, schemas, testes,
ferramentas e documentação do projeto. A árvore rastreada local tinha 97 arquivos e a árvore
remota do GitHub tinha os mesmos 97 caminhos, sem divergências. Não foi encontrada outra árvore de
código, protótipo ou patch exclusivo do LocalCoder fora do repositório oficial.

Não foram copiados modelos, pesos, caches grandes, credenciais, sessões ou código de AFolha,
TopazioAI ou qualquer outro projeto. Nenhum arquivo fora do LocalCoder foi apagado. Essa decisão
recuperou `0 bytes` e preservou qualquer material cuja proveniência pudesse ser ambígua.

## Área e método de busca

Foram inventariados os diretórios-raiz de `C:\` e `E:\`, com busca read-only por:

- nomes e conteúdo contendo `LocalCoder`, `localcoder`, `0xTPZ/LocalCoder` e referências ao
  caminho canônico;
- arquivos de código, scripts, schemas, documentação, patches, configurações e relatórios;
- metadados Git, tamanhos, datas, hashes e arquivos não rastreados;
- modelos `*.gguf` e executáveis de runtime apenas para classificação, nunca para cópia.

Windows, recycle bins, caches, ambientes, `node_modules`, binários de outros projetos, modelos e
runtime externo não foram tratados como fonte de código do LocalCoder. Projetos externos foram
consultados somente para confirmar referências de alto sinal; não foram modificados.

## Inventário classificado

O inventário de alto sinal contém 31 registros/grupos:

| Quantidade | Item | Classificação | Decisão |
|---:|---|---|---|
| 1 | `E:\LocalCoder` com 97 arquivos rastreados | `KEEP` | Fonte oficial; preservado e versionado |
| 5 | Textos de Missões 001–004 e desta consolidação em `%USERPROFILE%\.codex\attachments\<id>\Texto colado.txt` | `GENERATED` / `USER PROVIDED` | Preservados fora do repositório; não são código executável |
| 19 | Referências textuais em `E:\AFolha`, `E:\AlicePlatform`, `E:\Topazio`, `E:\TopazioAI` e `E:\TopazioMobileServerOS`, incluindo sessões de recuperação | `EXTERNAL` | Não importar, mover ou apagar |
| 4 | GGUF Qwen3 em `E:\TopazioAI\models` | `MODEL` | Mantidos somente no local externo; não copiados |
| 2 | `llama-server.exe` CPU/Vulkan em `E:\TopazioAI\runtime` | `EXTERNAL` | Runtime compartilhado externo; não copiado |

Os 19 registros externos incluem `E:\TopazioAI\profiles\localcoder\profile.json`. O nome
`localcoder` nesse caminho é um perfil de integração do TopazioAI, não uma implementação do
LocalCoder; por isso foi classificado como `EXTERNAL` e não foi incorporado.

As referências externas foram encontradas em documentação, perfis e histórico de recuperação,
não em uma segunda implementação rastreável. A busca não identificou itens `IMPORT` ou `MERGE`.

## Comparação e consolidação

- `HEAD` antes da auditoria: `eb0a17efdaf9b755d7d0af7cb1d13accbe33a7d5`.
- A árvore local tinha 97 blobs e a árvore `main` no GitHub tinha 97 blobs.
- Caminhos locais ausentes no remoto: `0`.
- Caminhos remotos ausentes localmente: `0`.
- Arquivos rastreados acima de 50 MiB: `0`.
- Arquivos não rastreados no fechamento da inspeção inicial: `0`.
- Itens importados: `0`.
- Itens mesclados: `0`.
- Duplicatas seguras removidas: `0`.
- Arquivos excluídos: `0`.
- Espaço recuperado: `0 bytes`.

A ausência de importação é intencional: o conteúdo candidato fora do repositório era entrada de
missão, referência histórica, perfil de outro sistema ou infraestrutura/modelo externo. Não havia
uma versão divergente de código do LocalCoder que pudesse ser mesclada com segurança.

## Reconstruibilidade

| Dependência | Classificação | Evidência |
|---|---|---|
| Código Python, entrypoint, schemas e contratos | `VERSIONED` | `src/`, `schemas/`, `pyproject.toml` |
| Testes determinísticos e Crash Lab | `VERSIONED` / `REPRODUCIBLE` | `tests/` e suíte `unittest` |
| Scanner, benchmark harness e laboratório | `VERSIONED` | `tools/`, `src/localcoder/benchmarks/`, configuração de exemplo |
| Documentação, decisões, roadmap e handoff | `VERSIONED` | `README.md`, `docs/`, `AGENTS.md` |
| Python 3.12+ e Git | `REPRODUCIBLE` | requisitos documentados; sem dependências de runtime obrigatórias |
| `llama.cpp` e modelos Qwen3 | `DOCUMENTED EXTERNAL DEPENDENCY` | existem em `E:\TopazioAI`, deliberadamente fora do Git |
| Credenciais, tokens e sessões | `SECRET/USER PROVIDED` | não são necessários para a suíte e não foram adicionados |
| Componente necessário ausente | — | nenhum para testes e reconstrução do núcleo |

Reconstrução mínima do núcleo a partir do clone:

```powershell
Set-Location E:\LocalCoder
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

O laboratório real de inferência exige o runtime e um modelo externo já existente; isso não é
necessário para reconstruir, testar ou manter a fundação do LocalCoder.

## Segurança e arquivos gerados

- O scanner de segredos passou; nenhum segredo foi promovido ao repositório.
- A configuração versionada do gateway é somente exemplo, local-only e sem credenciais.
- `__pycache__`, `.venv`, estado, logs e resultados de benchmark permanecem cobertos pelo
  `.gitignore`; resultados locais do laboratório foram preservados como evidência operacional,
  não como parte da fonte reproduzível.
- GGUF, pesos, caches grandes, ambientes virtuais, sessões do Codex e credenciais nunca devem ser
  copiados para o repositório. Modelos e runtimes locais só podem ser referenciados por uma
  configuração sanitizada e documentação.
- Nenhuma operação de limpeza tocou Windows, recycle bins, AFolha, TopazioAI ou outros projetos.

## Verificações finais

Foram executados ou confirmados:

- suíte completa de testes, incluindo Crash Lab e testes de schemas;
- `compileall` para `src`, `tests` e `tools`;
- scanner `tools/check_secrets.py`;
- `git diff --check`;
- auditoria de arquivos grandes e não rastreados;
- comparação da árvore local com `0xTPZ/LocalCoder/main`;
- verificação de processos/listeners do laboratório LocalCoder;
- verificação read-only de que nenhum comando da missão escreveu em AFolha ou TopazioAI. O
  `TopazioAI` permaneceu limpo; `AFolha` estava limpo no inventário inicial além de `ahead 1`, mas
  apresentou alterações e arquivos não rastreados durante a janela final. Esse trabalho externo
  foi preservado, não foi atribuído à missão e não foi usado na consolidação; portanto, o estado
  limpo final de AFolha não é afirmado.

O worker observado anteriormente em TopazioAI é uma responsabilidade externa e não foi
interrompido, consultado ou usado como parte da consolidação. A próxima missão continua sendo a
Missão 005, mas não foi iniciada nesta auditoria.
