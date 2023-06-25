from abc import ABC, abstractmethod
from tinkoff.invest import Client


class BrokerClient(ABC):
    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass


