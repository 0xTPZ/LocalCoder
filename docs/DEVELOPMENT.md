# Desenvolvimento

## Requisitos

- Windows ou ambiente compatível com Python 3.12+.
- Git.
- Nenhuma dependência de runtime obrigatória; schemas, redaction e persistência usam a biblioteca
  padrão.

Node.js, runtimes de inferência, GPUs e ferramentas externas não são necessários para executar os
testes das Missões 001, 002 e 003.

## Verificação local

```powershell
Set-Location E:\LocalCoder
python -m unittest discover -s tests -v
python tools\check_secrets.py
python -m compileall -q src tests tools
git diff --check
git status --short
```

Se o pacote for executado diretamente sem instalação, o entrypoint de teste injeta `src` no
`sys.path`. Para uso normal, utilize um ambiente virtual e `pip install --no-deps -e .`.

## Fluxo de mudança

1. Ler `AGENTS.md`, o roadmap e o handoff.
2. Identificar a missão e seu fora de escopo.
3. Preservar mudanças existentes; não usar reset destrutivo.
4. Implementar em pequenos commits coerentes.
5. Executar testes, scanner, diff check e inspeção de segredos.
6. Atualizar decisões, changelog e handoff.
7. Registrar evidência e o resultado `PASS`, `FAIL`, `BLOCKED` ou `NOT TESTED`.

Para validar schemas diretamente:

```powershell
python -c "import sys; sys.path.insert(0, 'src'); from localcoder.schemas import SchemaRegistry; print(SchemaRegistry().names())"
```

O Crash Lab é executado dentro da suíte e usa somente subprocessos próprios em diretórios
temporários. Ele pode criar locks/temporários abandonados nesses diretórios, que são removidos
pela limpeza do teste; não mata processos do sistema.

## Dependências

Não adicionar uma dependência para resolver algo que a biblioteca padrão cubra razoavelmente.
Quando uma dependência for necessária, registrar versão, licença, motivo, superfície de risco,
alternativa e procedimento de atualização.

## Commits

Commits devem ser pequenos, relacionados à missão e descritivos. Não force push e não altere
histórico remoto. Antes do primeiro push, executar auditoria de segredos, revisar todo o diff,
confirmar `.gitignore` e rodar os testes.
