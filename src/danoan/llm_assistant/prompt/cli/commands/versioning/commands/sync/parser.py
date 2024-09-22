import argparse


def __sync__(*args, **kwargs):
    """
    Sync prompt repository configuration with local folder.
    """
    from danoan.llm_assistant.prompt.cli.commands.versioning.commands.sync import (
        action as A,
    )

    A.sync()


def extend_parser(subparser_action=None):
    command_name = "sync"
    description = __sync__.__doc__
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

    parser.set_defaults(func=__sync__, subcommand_help=parser.print_help)

    return parser
