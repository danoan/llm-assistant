from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import threading
from queue import Queue
from typing import Any, Callable, Dict, Optional


RegisterListenerFunction = Callable[[str, Callable[..., Any]], Any]
UnregisterListenerFunction = RegisterListenerFunction


class EventNotifier:
    """
    Helper class that notifies caller when an event is complete.

    The EventNotifier is usually returned by an external class
    (let us say Manager) that accepts registering listeners to
    its events. A common use is to create a context and check
    the value of the notifier.

    with Manager.get_notifier(event_name) as notifier:
        while True:
            if notifier.is_set():
                break
            do_something()
    """

    def __init__(
        self,
        event_name: str,
        register_fn: RegisterListenerFunction,
        unregister_fn: UnregisterListenerFunction,
    ):
        self.event_name = event_name
        self._event = threading.Event()
        self._register = register_fn
        self._unregister = unregister_fn

    def _callback(self, **kwargs):
        self._event.set()

    def __enter__(self):
        self._register(self.event_name, self._callback)
        return self._event

    def __exit__(self, exc_type, exc_value, traceback):
        self._unregister(self.event_name, self._callback)


class TaskListenerNotRegisteredError(Exception):
    pass


class Task(ABC):
    """
    Represent a task of TaskRunner.
    """

    class Event(Enum):
        Stop = "stop"
        Complete = "complete"

    def __init__(self):
        self._listeners = {}

    def _trigger_event(self, event: Event, **kwargs):
        if event not in self._listeners:
            return

        for callback in self._listeners[event]:
            callback(**kwargs)

    def _run(self, **kwargs):
        output = self.run(**kwargs)
        self._trigger_event(Task.Event.Complete, output=output)
        return output

    @abstractmethod
    def run(self, **kwargs):
        """
        The task logic.
        """
        ...

    def start(self, **kwargs):
        """
        Start executing the task logic.

        It triggers all listeners of Task.Event.Complete whenever
        is finished.
        """
        return self._run(**kwargs)

    def stop(self):
        """
        Trigger all listeners of event Task.Event.Stop.

        The logic contained in run is not aborted.
        It is up to the user to take this decision.

        # Run logic
        with self.get_event_notifier(Task.Event.Stop) as notifier:
            if notifier.is_set():
                take action
        """
        self._trigger_event(Task.Event.Stop)

    def register_listener(self, event: Event, callback):
        """
        Register a callback function to be called whenever the event is triggered.
        """
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

    def unregister_listener(self, event: Event, callback):
        """
        Unregister a previously registered listener.

        Raises:
            TaskListenerNotRegisteredError if the listener to unregister is not found.
        """
        if event not in self._listeners:
            raise TaskListenerNotRegisteredError()

        filter_result = filter(lambda x: x is callback, self._listeners[event])
        self._listeners[event] = list(filter_result)

    def get_event_notifier(self, event: Event) -> EventNotifier:
        """
        Create EventNotifier for an event.

        The EventNotifier allows us to check if events such as Task.Event.Complete or
        Task.Event.Stop were triggered.
        """

        def _register(event_name: str, callback):
            self.register_listener(Task.Event(event_name), callback)

        def _unregister(event_name: str, callback):
            self.unregister_listener(Task.Event(event_name), callback)

        return EventNotifier(event.value, _register, _unregister)


class TaskNotRegisteredError(Exception):
    pass


@dataclass
class TaskInstruction:
    task_name: str
    task_input: Optional[Dict[str, Any]]


class TaskRunner:
    """
    Execute TaskInstruction added to its queue until emptness.

    TaskRunner executes tasks in the same order they are added in its internal
    queue via a TaskInstruction. The TaskInstruction contains the task name and
    its input variables. To execute a task, the latter needs to be priorly
    registered.

    The Task output is an optional TaskInstruction and it is added to the
    TaskRunner queue as soon it is completed. The added TaskInstruction is
    then executed in the next turn.

    The queue object is adapted to concurrent thread execution.
    """

    QuitInstruction = TaskInstruction("quit", None)

    def __init__(self):
        self._nodes: Dict[str, Optional[Task]] = {}
        self._callback: Dict[str, Any] = {}
        self._task_queue: Queue = Queue()
        self._current_task: Optional[str] = None

    def _register_task(self, task_name: str, task: Task, callback=None):
        self._nodes[task_name] = task
        self._callback[task_name] = callback

    def register(self, task_name: str, first_task: bool = False, callback=None):
        """
        Decorator to register a function as a task.
        """

        def decorator(func):
            class _Task(Task):
                def run(self, **kwargs):
                    return func(self, **kwargs)

            self._register_task(task_name, _Task(), callback)
            if first_task:
                self._task_queue = Queue()
                self._task_queue.put(TaskInstruction(task_name, None))

        return decorator

    def run(self):
        """
        Traverse the queue executing all tasks there present.
        """
        while not self._task_queue.empty():
            td = self._task_queue.get()
            if not td:
                continue

            if td == TaskRunner.QuitInstruction:
                break

            task = self._nodes[td.task_name]
            if not task:
                continue
            self._current_task = td.task_name

            if self._callback[td.task_name]:
                self._callback[td.task_name](td.task_input)

            input_dict = {}
            if td and td.task_input:
                input_dict = td.task_input

            self._task_queue.put(task.start(**input_dict))

    def next(self):
        """
        Stop the current task.
        """
        if not self._current_task:
            return
        task = self._nodes[self._current_task]
        if task:
            task.stop()

    def add(self, td: TaskInstruction):
        """
        Add a new TaskInstruction to the queue.
        """
        if td.task_name not in self._nodes:
            raise TaskNotRegisteredError()
        self._task_queue.put(td)

    def stop(self):
        """
        Stop all tasks.
        """
        self._task_queue.put(TaskRunner.QuitInstruction)

    def clear(self):
        """
        Clear task queue.
        """
        while not self._task_queue.empty():
            self._task_queue.get()
