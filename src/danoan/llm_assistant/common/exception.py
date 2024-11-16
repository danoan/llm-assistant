"""
Shared exceptions between prompt and runner modules.
"""


class EnvironmentVariableNotDefinedError(Exception):
    pass


class ConfigurationFileDoesNotExistError(Exception):
    pass
