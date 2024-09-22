import argparse


def __regenerate_tests__(prompt_name: str, *args, **kwargs):
    """
    Run all tests and replace stored results.
    """
    from danoan.llm_assistant.prompt.cli.commands.evaluate.commands.regenerate_tests import (
        action as A,
    )

    A.regenerate_tests(prompt_name)


def extend_parser(subparser_action=None):
    command_name = "regenerate-tests"
    description = __regenerate_tests__.__doc__
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

    parser.add_argument("prompt_name", type=str, help="Prompt name")
    parser.set_defaults(func=__regenerate_tests__, subcommand_help=parser.print_help)

    return parser
