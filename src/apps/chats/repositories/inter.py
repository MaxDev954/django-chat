from abc import ABC, abstractmethod
from typing import Dict


class IMessageRepo(ABC):
    @abstractmethod
    def push_message(self, conv_id: str, message: Dict):
        pass

    @abstractmethod
    def get_messages(self, conv_id: str) -> list[Dict]:
        pass

    @abstractmethod
    def get_messages_by_user_id(self, conv_id:str,  user_id:int|str) -> list[Dict]:
        pass

class IMessageClearRepo(IMessageRepo, ABC):
    @abstractmethod
    def clear_messages(self, conv_id: str):
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

    @abstractmethod
    def delete_set(self, key:str):
        pass