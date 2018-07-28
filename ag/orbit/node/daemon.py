#!/usr/bin/env python3
#
# Copyright (C) 2018 Alpha Griffin
# @%@~LICENSE~@%@


def run():
    print("Continuously processing all blocks...")
    pass


if __name__ == '__main__':
    from contextlib import suppress
    from sys import argv

    with suppress(KeyboardInterrupt):
        print()
        run()

