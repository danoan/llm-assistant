from danoan.llm_assistant.prompt.cli.commands.versioning import parser as versioning
from danoan.llm_assistant.prompt.cli.commands.evaluate import parser as evaluate

import argparse


def main():
    parser = argparse.ArgumentParser(
        "prompt-evaluator",
        description="Collection of tools to evaluate and versioning prompts",
    )
    subparser_action = parser.add_subparsers()

    list_of_commands = [evaluate, versioning]
    for command in list_of_commands:
        command.extend_parser(subparser_action)

    args = parser.parse_args()
    if "func" in args:
        args.func(**vars(args))
    elif "subcommand_help" in args:
        args.subcommand_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
