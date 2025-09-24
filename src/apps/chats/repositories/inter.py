from abc import ABC, abstractmethod
from typing import Dict


class IMessageRepo(ABC):
    @abstractmethod
    def push_message(self, conv_id: str, message: Dict):
        pass

    @abstractmethod
    def get_messages(self, conv_id: str) -> list[Dict]:
        pass

class IConsumerRepo(ABC):
    @abstractmethod
    def add_to_set(self, key: str, value: str):
        pass

    @abstractmethod
    def remove_from_set(self, key: str, value: str):
        pass

    @abstractmethod
    def get_set_members(self, key: str):
        pass