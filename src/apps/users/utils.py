import random


def generate_random_color():
    def rand_channel():
        return random.randint(64, 192)

    return '#{0:02X}{1:02X}{2:02X}'.format(rand_channel(), rand_channel(), rand_channel())