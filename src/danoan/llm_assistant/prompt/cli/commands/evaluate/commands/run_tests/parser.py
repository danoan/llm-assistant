import argparse


def __run_tests__(prompt_name: str, *args, **kwargs):
    """
    Run tests for a prompt and generate a report.
    """
    from danoan.llm_assistant.prompt.cli.commands.evaluate.commands.run_tests import (
        action as A,
    )

    A.run_tests(prompt_name)


def extend_parser(subparser_action=None):
    command_name = "run-tests"
    description = __run_tests__.__doc__
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
    parser.set_defaults(func=__run_tests__, subcommand_help=parser.print_help)

    return parser
