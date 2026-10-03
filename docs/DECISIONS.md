# Registro de decisões

## ADR-001 — Fundação independente em Python

- **Status:** vigente.
- **Decisão:** usar Python 3.12, biblioteca padrão no runtime inicial e um monólito modular.
- **Motivo:** reduz dependências e permite desenvolver contratos antes de escolher runtime/modelo.
- **Consequência:** adapters e persistência ainda precisam ser construídos.
- **Alternativas rejeitadas:** copiar estrutura interna de AFolha/TopazioAI; acoplar ao Node;
  escolher um modelo definitivo.

## ADR-002 — Modelo como backend substituível

- **Status:** vigente.
- **Decisão:** o núcleo conhece `ModelBackend`, `ModelProfile`, request e result normalizados.
- **Motivo:** a missão exige comparar modelos por qualidade, custo computacional, estabilidade
  e uso de ferramentas.
- **Consequência:** capacidades específicas devem ser declaradas, não presumidas.

## ADR-003 — Resource Manager sem heurística nesta missão

- **Status:** vigente.
- **Decisão:** registrar estados e portas, sem thresholds ou decisões automáticas.
- **Motivo:** o pedido exige estudar o ambiente antes de implementar heurísticas arbitrárias.
- **Evidência ambiental:** hardware e estado do controlador existente foram inventariados no
  relatório da Missão 001, mas não são política do LocalCoder.

## ADR-004 — Referência técnica sem dependência estrutural

- **Status:** vigente.
- **Decisão:** reutilizar conceitos documentados de contratos, filas, estado `UNLOADED`,
  validação, idempotência e resource-awareness; reimplementar no LocalCoder quando necessário.
- **Motivo:** AFolha e TopazioAI têm consumidores e ciclos de vida próprios.
- **Consequência:** qualquer futura integração deve ocorrer por adapter/contrato versionado.

## ADR-005 — Capacidades deny-by-default

- **Status:** vigente.
- **Decisão:** filesystem write, execução de processos, rede, navegador, SSH, e-mail e redes
  sociais começam negados e separados.
- **Motivo:** autonomia não deve significar irreversibilidade ou expansão silenciosa de acesso.

## ADR-006 — Licença pública pendente

- **Status:** decisão humana necessária.
- **Decisão atual:** não escolher uma licença por inferência; não criar `LICENSE` ainda.
- **Motivo:** “open source” não determina sozinho MIT, Apache-2.0, GPL ou outra licença.
- **Próximo passo:** escolher licença antes de anunciar o repositório como pronto para consumo.
