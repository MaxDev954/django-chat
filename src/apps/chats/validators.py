from typing import Dict


def validate_message_required_field(message: Dict):
    required_keys = {'sender', 'text', 'timestamp'}
    if not all(key in message for key in required_keys):
        return False
    return True
