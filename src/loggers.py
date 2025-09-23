import logging

_django_logger = logging.getLogger('django')
_redis_logger = logging.getLogger('redis')
_general_logger = logging.getLogger('general')

get_django_logger = lambda : _django_logger
get_redis_logger = lambda : _redis_logger
get_general_logger = lambda : _general_logger
