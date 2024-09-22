from danoan.llm_assistant.prompt.core import api
import argparse
import git
from pathlib import Path


def __track__(repository_url: str, *args, **kwargs):
    """
    Clone a prompt repository and start to track it.
    """
    repository_name = Path(repository_url).stem
    prompts_folder = api.get_prompts_folder()

    if repository_name in map(lambda x: x.name, api.get_tracked_prompts()):
        print("Prompt is tracked already")
        exit(0)

    local_folder = prompts_folder / repository_name
    git.Repo.clone_from(repository_url, local_folder)


def extend_parser(subparser_action=None):
    command_name = "track"
    description = __track__.__doc__
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

    parser.add_argument(
        "repository_url", type=str, help="URL to git repository containing the prompt"
    )

    parser.set_defaults(func=__track__, subcommand_help=parser.print_help)

    return parser
