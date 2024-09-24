from danoan.llm_assistant.runner.cli.commands.session.task_runner import (
    TaskRunner,
    Task,
    TaskInstruction,
)

from queue import Queue
import pytest
import time
import threading


def test_sm_cycle():
    st_welcome = "Welcome"
    st_select_message = "SelectMessage"
    st_read_message = "ReadMessage"

    MESSAGE = "Your travel plan to Greece is ready."

    tr = TaskRunner()

    @tr.register(st_welcome, first_task=True)
    def welcome(task: Task) -> TaskInstruction:
        return TaskInstruction(st_select_message, None)

    @tr.register(st_select_message)
    def select_message(task: Task) -> TaskInstruction:
        return TaskInstruction(st_read_message, {"message": MESSAGE})

    @tr.register(st_read_message)
    def read_message(task: Task, message: str) -> TaskInstruction:
        assert message == MESSAGE
        return None

    tr.run()


def test_stop():
    buffer_queue: Queue = Queue()

    def register_states(tr: TaskRunner):
        @tr.register("state_a", first_task=True)
        def state_a(self):
            buffer_queue.put("start: state_a")

            with self.get_event_notifier(Task.Event.Stop) as event_notifier:
                event_notifier.wait()

            buffer_queue.put("end: state_a")
            return TaskInstruction("state_b", {"message": "Euro"})

        @tr.register("state_b")
        def state_b(self, *, message):
            print("Enter B")
            buffer_queue.put("start: state_b")
            buffer_queue.put(f"message: {message}")

            with self.get_event_notifier(Task.Event.Stop) as event_notifier:
                event_notifier.wait()

            buffer_queue.put("end: state_b")
            return None

    tr = TaskRunner()
    register_states(tr)
    t = threading.Thread(target=tr.run)
    t.start()  # Enter A

    time.sleep(0.1)
    tr.next()  # Quit A: Enter B
    time.sleep(0.1)

    tr.add(TaskInstruction("state_a", None))  # Add A; Quit B; Add None;Enter A
    tr.next()
    time.sleep(0.1)
    tr.next()  # Quit A; Enter B
    time.sleep(0.1)
    tr.next()
    t.join()

    assert buffer_queue.get() == "start: state_a"
    assert buffer_queue.get() == "end: state_a"
    assert buffer_queue.get() == "start: state_b"
    assert buffer_queue.get() == "message: Euro"
    assert buffer_queue.get() == "end: state_b"

    assert buffer_queue.get() == "start: state_a"
    assert buffer_queue.get() == "end: state_a"
    assert buffer_queue.get() == "start: state_b"
    assert buffer_queue.get() == "message: Euro"
    assert buffer_queue.get() == "end: state_b"
