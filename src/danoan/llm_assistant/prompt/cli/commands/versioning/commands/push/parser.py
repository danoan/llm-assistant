import argparse
from typing import Optional


def __push__(prompt_name: str, version: Optional[str] = None, *args, **kwargs):
    """
    Push a new prompt version.

    The version of a prompt is made of three components.
        prompt_id.major.minor

    The prompt_id identifies a prompt variation. For example,
    we may have a prompt to correct text in some language. The
    1.x.x series could be dedicated to very simplistic versions
    of these prompts that only return the corrected version. The
    2.x.x series could be dedicated to versions in which besides
    the correction, the prompt also gives the explanation and
    so on.

    We bump minor every time one of the following situations:
        - Add more examples
        - Any edition on user and system prompts that do
          not modify the input neither output structure.
    We bump the major every time we do one of the following:
        - Update input or output structure.
    """
    from danoan.llm_assistant.prompt.cli.commands.versioning.commands.push import (
        action as A,
    )

    A.push(prompt_name, version)


def extend_parser(subparser_action=None):
    command_name = "push"
    description = __push__.__doc__
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

    parser.add_argument("prompt_name", type=str)
    parser.add_argument("--version", type=str)

    parser.set_defaults(func=__push__, subcommand_help=parser.print_help)

    return parser
