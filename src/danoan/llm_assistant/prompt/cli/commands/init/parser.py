from danoan.llm_assistant.common import api as common
from danoan.llm_assistant.prompt.core import api, model

import argparse
from dataclasses import asdict
from pathlib import Path
import toml


def __init__(*args, **kwargs):
    """
    Make the current directory the container of all prompt repositories.
    """
    config_filepath = common.get_configuration_filepath()
    if config_filepath.exists():
        print(f"The configuration file exists already")
        exit(1)

    config = model.Configuration(str(Path.cwd()))
    with open(config_filepath, "w") as f:
        toml.dump(asdict(config), f)

    prompts_folder = Path.cwd() / "prompts"
    prompts_folder.mkdir(parents=True, exist_ok=True)


def extend_parser(subparser_action=None):
    command_name = "init"
    description = __init__.__doc__
    help = description.split(".")[0] if description else ""

    if subparser_action:
        parser = subparser_action.add_parser(
            command_name,
            help=help,
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
    else:
        parser = argparse.ArgumentParser(
            command_name,
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

    parser.set_defaults(func=__init__, subcommand_help=parser.print_help)

    return parser
