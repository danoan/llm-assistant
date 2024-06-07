from danoan.llm_assistant.cli.commands import custom, setup

import argparse


def main():
    parser = argparse.ArgumentParser(
        "llm-assistant", description="Collection of LLM applications"
    )
    subcommand_action = parser.add_subparsers()

    list_of_commands = [setup, custom]
    for command in list_of_commands:
        command.extend_parser(subcommand_action)

    args = parser.parse_args()
    if "func" in args:
        args.func(**vars(args))
    elif "subommand_help" in args:
        args.subommand_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
