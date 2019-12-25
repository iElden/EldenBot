

class ConfigurerException(Exception):
    """Base Exception for configurer"""

class MissingValue(ConfigurerException):
    """Missing value in query"""

class InvalidValue(ConfigurerException):
    """Value is invalid for this format"""

class InvalidCommand(ConfigurerException):
    """La commande n'est pas reconnu"""

class VariableNotFound(ConfigurerException):
    """Variable non trouvée"""