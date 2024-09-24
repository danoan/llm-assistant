from danoan.llm_assistant.common import api as common
from danoan.llm_assistant.runner.core import model

from dataclasses import asdict
import logging
import sys
import toml

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


def init(reset: bool = False):
    config_folder = common.get_configuration_folder()
    if not config_folder.exists():
        config_folder.mkdir(parents=True, exist_ok=True)

    config_path = common.get_configuration_filepath()
    if not config_path.exists() or reset:
        config = model.LLMAssistantConfiguration()
        with open(config_path, "w") as f:
            toml.dump(asdict(config), f)
