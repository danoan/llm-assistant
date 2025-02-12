import argparse

from typing import Optional


def __run_tests__(
    prompt_name: str,
    no_cache: bool = False,
    base_version: Optional[str] = None,
    compare_version: Optional[str] = None,
    *args,
    **kwargs,
):
    """
    Run tests for a prompt and generate a report.
    """
    from danoan.llm_assistant.prompt.cli.commands.evaluate.commands.run_tests import (
        action as A,
    )

    use_cache = not no_cache
    if not base_version:
        base_version = "current"
    if not compare_version:
        compare_version = "current"

    A.run_tests(prompt_name, use_cache, base_version, compare_version)


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
    parser.add_argument("--no-cache", action="store_true", help="Do not use the cache")
    parser.add_argument(
        "--base-version", "-b", help="Prompt version to be used as base"
    )
    parser.add_argument(
        "--compare-version", "-c", help="Prompt version to be compared with"
    )
    parser.set_defaults(func=__run_tests__, subcommand_help=parser.print_help)

    return parser
