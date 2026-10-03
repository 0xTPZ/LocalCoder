"""Erros públicos de schema e estado persistente."""


class SchemaError(ValueError):
    """Base para erros de contrato persistente."""


class SchemaNotFoundError(SchemaError):
    pass


class SchemaValidationError(SchemaError):
    pass


class UnknownSchemaVersionError(SchemaError):
    """A versão é futura/desconhecida e não pode ser interpretada silenciosamente."""


class UnsupportedSchemaVersionError(SchemaError):
    """A versão é conhecida, mas não é suportada pela implementação atual."""


class StateCorruptionError(SchemaError):
    """O arquivo existe, mas não representa um documento recuperável."""
