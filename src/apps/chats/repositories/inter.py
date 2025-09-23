from abc import ABC, abstractmethod
from typing import Dict


class IMessageRepo(ABC):
    @abstractmethod
    def push_message(self, conv_id: str, message: Dict):
        pass

    @abstractmethod
    def get_messages(self, conv_id: str) -> list[Dict]:
        pass