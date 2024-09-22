import argparse


def __list__(*args, **kwargs):
    """
    List all tracked prompts.
    """
    from danoan.llm_assistant.prompt.cli.commands.versioning.commands.list import (
        action as A,
    )

    A.list_prompts()


def extend_parser(subparser_action=None):
    command_name = "list"
    description = __list__.__doc__
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

    parser.set_defaults(func=__list__, subcommand_help=parser.print_help)

    return parser
