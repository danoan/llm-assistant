from danoan.llm_assistant.core import api, exception


def ensure_environment_variable_is_defined(logger):
    try:
        api.get_configuration_folder()
    except exception.EnvironmentVariableNotDefinedError:
        logger.error(
            f"The environment variable {api.LLM_ASSISTANT_ENV_VARIABLE} is not defined. Please define it before proceeding."
        )
        exit(1)


def ensure_configuration_file_exist(logger):
    ensure_environment_variable_is_defined(logger)
    try:
        api.get_configuration()
    except exception.ConfigurationFileDoesNotExistError:
        logger.error(
            f"The file {api.get_configuration_filepath()} was not found. You can create one by calling llm-assistant setup init"
        )
        exit(1)
