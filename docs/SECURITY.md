# Segurança

## Baseline da fundação

- O núcleo não executa comandos, acessa rede, abre navegador, usa SSH ou carrega modelos.
- Capacidades são enumeradas e negadas por padrão.
- `.gitignore` exclui ambientes locais, segredos, logs, checkpoints e artefatos grandes.
- O scanner `tools/check_secrets.py` detecta padrões de alto sinal antes do commit.
- `localcoder.state.redaction` remove campos sensíveis, bearer/cookie headers, credenciais em URLs,
  query secrets e padrões de tokens antes de expor eventos/resultados.
- `AuditEvent.to_document()` e `MemoryAuditTrail.append()` aplicam redaction; testes usam somente
  fixtures construídas, não segredos reais.
- `AtomicJsonStore` valida o novo estado e só substitui o arquivo anterior após flush/fsync.
- `FileLock` falha em conflito e não remove lock stale automaticamente; `RecoveryManager` não
  executa ações e bloqueia estado ambíguo/corrompido.
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
| Corrupção de estado JSON | Validação, temporário e troca atômica | PASS na Missão 002 |
| Exposição por rede | Nenhuma integração de rede | PASS para a fundação |
| Modelo malicioso/artefato não verificado | Não há download/loader | NÃO IMPLEMENTADO |
| Repetição após crash | Journal + estado AMBIGUOUS sem auto-repeat | PASS na Missão 003 |
| Concorrência local | Lock exclusivo com stale explícito | PASS na Missão 003 |

## Regras para missões futuras

1. Nunca registrar valores de tokens, senhas, cookies, chaves ou credenciais.
2. Redigir erros externos antes de audit/log.
3. Limitar tempo, tentativas, tamanho, escopo de filesystem e consumo de recursos.
4. Validar origem/licença/hash de modelos e dependências antes de uso.
5. Separar preview/dry-run de aplicação efetiva.
6. Criar checkpoint antes de operações mutáveis e verificar rollback.
7. Parar em modo fail-closed quando autorização, contexto ou integridade forem incertos.
8. Preservar evidência de falhas e correções.

## Auditoria de segredos

Os resultados verificáveis estão nos relatórios das Missões 001, 002 e 003. A auditoria é limitada ao
repositório LocalCoder, exclui binários/modelos e deve ser complementada por revisão do diff e
checagem do conteúdo enviado ao GitHub.
