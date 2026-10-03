# Ferramentas de desenvolvimento

As ferramentas próprias do repositório devem ser pequenas, reproduzíveis e seguras por padrão.

`check_secrets.py` é um scanner heurístico de alto sinal. Antes de cada commit, combine seu
resultado com `git diff --check`, inspeção do diff completo e verificação de `.gitignore`.
