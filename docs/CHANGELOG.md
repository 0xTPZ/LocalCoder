# Changelog

## 0.2.0 — 2026-10-03

- Adotada Apache License 2.0.
- Adicionados schemas JSON v1 para as entidades persistentes da arquitetura.
- Adicionado `SchemaRegistry` com rejeição controlada de versões desconhecidas, estado inválido,
  campos ausentes e propriedades inesperadas.
- Adicionado `AtomicJsonStore` com validação, temporário no mesmo volume, flush/fsync e
  substituição atômica adequada ao Windows.
- Adicionados UUIDs estáveis, timestamps UTC, `CheckpointRecord`, lifecycle de operação e
  registry de idempotência.
- Adicionada redaction centralizada para estruturas, headers, URLs, tokens e erros.
- `AuditEvent` passou a ter contrato estruturado e redaction antes da representação persistível.
- Adicionados testes adversariais de truncamento, corrupção, repetição, conflito, redaction e
  interrupção simulada.

## 0.1.0 — 2026-10-03

- Criada a fundação do LocalCoder em `E:\LocalCoder`.
- Registrada auditoria não destrutiva de hardware, Windows, ferramentas, AFolha, TopazioAI,
  modelos locais e GitHub CLI.
- Criados contratos substituíveis para modelos, recursos, capacidades, projetos, missões,
  checkpoints e auditoria.
- Criada constituição operacional, roadmap verificável e documentação de segurança.
- Adicionado teste determinístico da fundação e scanner heurístico de segredos.
- Não implementados agente completo, inferência, downloads, scheduler, heurísticas de recursos,
  execução de comandos ou integrações externas.
