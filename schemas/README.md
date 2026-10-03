# Schemas versionados

Os documentos persistentes do LocalCoder usam `schema_version` inteiro no objeto raiz. A versão
atual é `1`, armazenada em `schemas/v1/`. O registry aceita somente versões explicitamente
suportadas; versões futuras desconhecidas e versões antigas sem suporte são rejeitadas de forma
controlada.

Os schemas usam JSON Schema Draft 2020-12 e são validados pelo validador mínimo próprio em
`src/localcoder/schemas/validator.py`. A implementação cobre deliberadamente apenas o subconjunto
necessário nesta missão, sem introduzir dependência externa.
