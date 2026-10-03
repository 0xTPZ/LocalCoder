# Segurança

## Baseline da fundação

- O núcleo não executa comandos, acessa rede, abre navegador, usa SSH ou carrega modelos.
- Capacidades são enumeradas e negadas por padrão.
- `.gitignore` exclui ambientes locais, segredos, logs, checkpoints e artefatos grandes.
- O scanner `tools/check_secrets.py` detecta padrões de alto sinal antes do commit.
- A revisão humana do diff continua obrigatória; scanner sem achados não é prova de ausência de
  segredo.
- Payloads de auditoria e checkpoint devem ser sanitizados pelo chamador.

## Threat model inicial

| Risco | Mitigação atual | Estado |
|---|---|---|
| Secret leak no Git | `.gitignore`, scanner, diff manual | Parcial; scanner heurístico |
| Ação irreversível | Nenhuma capacidade de escrita/execução ativada | PASS para a fundação |
| Prompt injection em projeto | Nenhum ingest/agent implementado | Não aplicável ainda |
| Loop infinito | Não há executor; roadmap exige limites | NÃO IMPLEMENTADO |
| Corrupção de checkpoint | Não há store durável | NÃO IMPLEMENTADO |
| Exposição por rede | Nenhuma integração de rede | PASS para a fundação |
| Modelo malicioso/artefato não verificado | Não há download/loader | NÃO IMPLEMENTADO |

## Regras para missões futuras

1. Nunca registrar valores de tokens, senhas, cookies, chaves ou credenciais.
2. Redigir erros externos antes de audit/log.
3. Limitar tempo, tentativas, tamanho, escopo de filesystem e consumo de recursos.
4. Validar origem/licença/hash de modelos e dependências antes de uso.
5. Separar preview/dry-run de aplicação efetiva.
6. Criar checkpoint antes de operações mutáveis e verificar rollback.
7. Parar em modo fail-closed quando autorização, contexto ou integridade forem incertos.
8. Preservar evidência de falhas e correções.

## Auditoria de segredos da Missão 001

O resultado verificável está no relatório em `docs/audits/MISSION-001-REPORT.md`. A auditoria é
limitada ao repositório LocalCoder, exclui binários/modelos e deve ser complementada por revisão
do diff e checagem do conteúdo enviado ao GitHub.
