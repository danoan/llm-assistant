from danoan.llm_assistant.runner.core import api
from danoan.llm_assistant.runner.cli.commands.session import session_core as core
from danoan.llm_assistant.runner.cli.commands.session.cli_drawer import CLIDrawer
from danoan.llm_assistant.runner.cli.commands.session import task_runner

from danoan.llm_assistant.common import model

from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
import toml
from types import SimpleNamespace
from typing import Deque


class MockCLIDrawer(CLIDrawer):
    def __init__(self):
        super().__init__()
        self.events: Deque = deque()
        self.prompt_value_queue: Deque = deque()

    def print_error(self, **kwargs):
        self.events.appendleft("print_error")

    def print_panel(self, **kwargs):
        self.events.appendleft("print_panel")

    def print_list(self, **kwargs):
        self.events.appendleft("print_list")

    def prompt(self, **kwargs):
        if len(self.prompt_value_queue) == 0:
            value = ""
        else:
            value = self.prompt_value_queue.pop()
        self.events.appendleft("prompt")
        return value

    def push_prompt_value(self, prompt_value):
        self.prompt_value_queue.appendleft(prompt_value)


@dataclass
class Context:
    prompt_repository: Path
    instances_folder: Path


def context(number_prompts: int):
    def create_prompt_config(prompt_repository: Path, prompt_name: str):
        prompt_config = model.PromptConfiguration(prompt_name, "", "", "")
        filepath = prompt_repository / prompt_name / "config.toml"
        filepath.parent.mkdir()
        with open(filepath, "w") as f_out:
            toml.dump(asdict(prompt_config), f_out)

    def create_instance(instances_folder: Path, prompt_name: str):
        prompt_instances_folder = instances_folder / prompt_name
        prompt_instances_folder.mkdir(exist_ok=True)
        print(prompt_instances_folder, prompt_instances_folder.exists())
        with open(prompt_instances_folder / "instance.toml", "w") as f:
            toml.dump({"name": "my-instance", "variables": {"language": "english"}}, f)

    def wrapper(fn):
        def inner():
            with TemporaryDirectory() as _prompt_repository:
                prompt_repository = Path(_prompt_repository)
                instances_folder = prompt_repository / "instances"
                instances_folder.mkdir()

                for i in range(number_prompts):
                    prompt_name = f"prompt-{i}"
                    create_prompt_config(prompt_repository, prompt_name)
                    create_instance(instances_folder, prompt_name)
                fn(Context(prompt_repository, instances_folder))

        return inner

    return wrapper


def get_prompt_config(prompt_repository: Path):
    p = list(prompt_repository.rglob("*config.toml"))[0]
    with open(p) as f:
        return model.PromptConfiguration(**toml.load(f))


def get_prompt_config_with_location(prompt_repository: Path):
    p = list(prompt_repository.rglob("*config.toml"))[0]
    return core.PromptConfigurationWithLocation(p, get_prompt_config(prompt_repository))


def get_prompt_instance(
    instances_folder: Path, prompt_config: model.PromptConfiguration
):
    instances_folder = instances_folder / prompt_config.name
    p = list(instances_folder.rglob("*.toml"))[0]
    with open(p) as f:
        return toml.load(f)


# -------------------- HelperFunctions --------------------


def test__retry_prompt_until_valid_int():
    cliDrawer = MockCLIDrawer()
    cliDrawer.push_prompt_value("non-integer")
    cliDrawer.push_prompt_value("0")
    cliDrawer.push_prompt_value("1")
    task = None
    core._retry_prompt_until_valid_int(
        "Enter an integer",
        1,
        10,
        cliDrawer,
        task,
    )
    assert cliDrawer.events.pop() == "prompt"
    assert cliDrawer.events.pop() == "print_error"
    assert cliDrawer.events.pop() == "prompt"
    assert cliDrawer.events.pop() == "print_error"
    assert cliDrawer.events.pop() == "prompt"


# -------------------- NoPromptSelected --------------------


def test_no_prompt_selected():
    @context(2)
    def inner(context: Context):
        cliDrawer = MockCLIDrawer()
        tr = task_runner.TaskRunner()
        core.register_tasks(
            cliDrawer,
            context.prompt_repository,
            tr.register,
        )

        cliDrawer.push_prompt_value("1")
        tr.stop()
        tr.run()
        assert len(cliDrawer.events) == 3
        assert cliDrawer.events.pop() == "print_panel"
        assert cliDrawer.events.pop() == "print_list"
        assert cliDrawer.events.pop() == "prompt"

    inner()


def test_no_prompt_selected_empty_prompt_repository():
    @context(0)
    def inner(context: Context):
        cliDrawer = MockCLIDrawer()
        tr = task_runner.TaskRunner()
        core.register_tasks(
            cliDrawer,
            context.prompt_repository,
            tr.register,
        )

        tr.stop()
        tr.run()
        assert len(cliDrawer.events) == 1
        assert cliDrawer.events.pop() == "print_error"

    inner()


# -------------------- PromptSelected --------------------


def test_prompt_selected():
    @context(2)
    def inner(context: Context):
        cliDrawer = MockCLIDrawer()
        tr = task_runner.TaskRunner()
        core.register_tasks(
            cliDrawer,
            context.prompt_repository,
            tr.register,
        )

        tr.clear()
        tr.add(
            task_runner.TaskInstruction(
                core.TaskName.PromptSelected,
                {
                    "prompt_config": get_prompt_config_with_location(
                        context.prompt_repository
                    )
                },
            )
        )
        cliDrawer.push_prompt_value("1")
        tr.stop()
        tr.run()
        assert len(cliDrawer.events) == 3
        assert cliDrawer.events.pop() == "print_panel"
        assert cliDrawer.events.pop() == "print_list"
        assert cliDrawer.events.pop() == "prompt"

    inner()


# -------------------- NewInstance --------------------


def test_new_instance():
    @context(2)
    def inner(context: Context):
        cliDrawer = MockCLIDrawer()
        tr = task_runner.TaskRunner()
        core.register_tasks(
            cliDrawer,
            context.prompt_repository,
            tr.register,
        )

        tr.clear()
        tr.add(
            task_runner.TaskInstruction(
                core.TaskName.NewInstance,
                {
                    "prompt_config": get_prompt_config_with_location(
                        context.prompt_repository
                    )
                },
            )
        )
        tr.stop()
        cliDrawer.push_prompt_value("my-instance")
        cliDrawer.push_prompt_value("language=portuguese")
        tr.run()
        assert len(cliDrawer.events) == 2
        assert cliDrawer.events.pop() == "prompt"
        assert cliDrawer.events.pop() == "prompt"

        # Existing instance
        tr.clear()
        tr.add(
            task_runner.TaskInstruction(
                core.TaskName.NewInstance,
                {
                    "prompt_config": get_prompt_config_with_location(
                        context.prompt_repository
                    )
                },
            )
        )
        tr.stop()
        cliDrawer.push_prompt_value("my-instance")
        cliDrawer.push_prompt_value("my-instance-2")
        cliDrawer.push_prompt_value("language=portuguese")
        tr.run()
        assert cliDrawer.events.pop() == "prompt"
        assert cliDrawer.events.pop() == "print_error"
        assert cliDrawer.events.pop() == "prompt"
        assert cliDrawer.events.pop() == "prompt"

        # # Assignment error
        tr.clear()
        tr.add(
            task_runner.TaskInstruction(
                core.TaskName.NewInstance,
                {
                    "prompt_config": get_prompt_config_with_location(
                        context.prompt_repository
                    )
                },
            )
        )
        tr.stop()
        cliDrawer.push_prompt_value("my-instance-3")
        cliDrawer.push_prompt_value("language")
        cliDrawer.push_prompt_value("language=portuguese,=")
        cliDrawer.push_prompt_value("language=portuguese,name=")
        cliDrawer.push_prompt_value("language=portuguese::name=machado")
        tr.run()
        assert cliDrawer.events.pop() == "prompt"
        assert cliDrawer.events.pop() == "prompt"
        assert cliDrawer.events.pop() == "print_error"
        assert cliDrawer.events.pop() == "prompt"
        assert cliDrawer.events.pop() == "print_error"
        assert cliDrawer.events.pop() == "prompt"
        assert cliDrawer.events.pop() == "print_error"
        assert cliDrawer.events.pop() == "prompt"

    inner()


# -------------------- LoadInstance --------------------


def test_load_instance():
    @context(2)
    def inner(context: Context):
        cliDrawer = MockCLIDrawer()
        tr = task_runner.TaskRunner()
        core.register_tasks(
            cliDrawer,
            context.prompt_repository,
            tr.register,
        )

        tr.clear()
        tr.add(
            task_runner.TaskInstruction(
                core.TaskName.LoadInstance,
                {
                    "prompt_config": get_prompt_config_with_location(
                        context.prompt_repository
                    )
                },
            )
        )
        tr.stop()
        cliDrawer.push_prompt_value("1")
        tr.run()
        assert len(cliDrawer.events) == 3
        assert cliDrawer.events.pop() == "print_panel"
        assert cliDrawer.events.pop() == "print_list"
        assert cliDrawer.events.pop() == "prompt"

    inner()


# -------------------- StartChat --------------------


def test_start_chat():
    @context(2)
    def inner(context: Context):
        cliDrawer = MockCLIDrawer()
        tr = task_runner.TaskRunner()
        core.register_tasks(
            cliDrawer,
            context.prompt_repository,
            tr.register,
        )

        prompt_config = get_prompt_config(context.prompt_repository)
        tr.clear()
        tr.add(
            task_runner.TaskInstruction(
                core.TaskName.StartChat,
                {
                    "prompt_config": prompt_config,
                    "instance": get_prompt_instance(
                        context.instances_folder, prompt_config
                    ),
                },
            )
        )
        tr.stop()
        cliDrawer.push_prompt_value("1")
        tr.run()
        assert len(cliDrawer.events) == 1
        assert cliDrawer.events.pop() == "print_panel"

    inner()


# -------------------- ContinueChat --------------------


def test_continue_chat(monkeypatch):
    @context(2)
    def inner(context: Context):
        cliDrawer = MockCLIDrawer()
        tr = task_runner.TaskRunner()
        core.register_tasks(
            cliDrawer,
            context.prompt_repository,
            tr.register,
        )

        def mock_custom(prompt_configuration, **prompt_variables):
            return SimpleNamespace(content=["j'adore écrire", "j'apprécie l'écriture"])

        monkeypatch.setattr(api, "custom", mock_custom)

        prompt_config = get_prompt_config(context.prompt_repository)
        tr.clear()
        tr.add(
            task_runner.TaskInstruction(
                core.TaskName.ContinueChat,
                {
                    "prompt_config": prompt_config,
                    "instance": get_prompt_instance(
                        context.instances_folder, prompt_config
                    ),
                },
            )
        )
        tr.stop()
        cliDrawer.push_prompt_value("j'aime écrire")
        cliDrawer.push_prompt_value("$$")
        tr.run()
        assert len(cliDrawer.events) == 4
        assert cliDrawer.events.pop() == "prompt"
        assert cliDrawer.events.pop() == "prompt"
        assert cliDrawer.events.pop() == "print_panel"
        assert cliDrawer.events.pop() == "print_panel"

    inner()
