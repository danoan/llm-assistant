from abc import ABC, abstractmethod


class CLIDrawer(ABC):
    @abstractmethod
    def print_error(self, **kwargs):
        pass

    @abstractmethod
    def print_panel(self, **kwargs):
        pass

    @abstractmethod
    def print_list(self, **kwargs):
        pass

    @abstractmethod
    def prompt(self, **kwargs):
        pass
