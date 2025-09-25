class MessageValidationError(Exception):
    pass

class MessageStorageError(Exception):
    pass

class MessageRetrievalError(Exception):
    pass

class ConversationNotFoundError(Exception):
    pass

class ConversationAccessDeniedError(Exception):
    pass

class TooManyMessageException(Exception):
    pass