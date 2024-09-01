import argparse


def __session__(*args, **kwargs):
    """
    Chat interface to interact with pre-registered prompts.

    To start a chat session the prompt must need to be stored
    in the prompt repository folder, configurable from the
    application settings.

    Ctrl+B: restart the session
    Ctrl+Q: exit the session
    """

    from danoan.llm_assistant.cli.commands.session import session as S

    S.start_session()


def extend_parser(subparser_action=None):
    command_name = "session"
    description = __session__.__doc__
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

    parser.set_defaults(func=__session__, subcommand_help=parser.print_help)

    return parser
