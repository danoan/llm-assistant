import logging
import sys
from dataclasses import asdict

import toml

from danoan.llm_assistant.common import config
from danoan.llm_assistant.runner.core import model

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


def init(reset: bool = False):
    config_folder = config.get_configuration_folder()
    if not config_folder.exists():
        config_folder.mkdir(parents=True, exist_ok=True)

    config_path = config.get_configuration_filepath()
    if not config_path.exists() or reset:
        llma_config = model.LLMAssistantConfiguration()
        with open(config_path, "w") as f:
            toml.dump(asdict(llma_config), f)
