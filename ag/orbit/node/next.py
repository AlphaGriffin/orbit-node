#!/usr/bin/env python3
#
# Copyright (C) 2018 Alpha Griffin
# @%@~LICENSE~@%@

from ag.orbit.node.config import get_rpc_url
from ag.orbit.node.sync import Process


def run(args):
    if args is not None and len(args) > 0:
        raise ValueError("Not expecting any arguments")

    print()
    print('Sync next block...')
    print()

    sync = Process(get_rpc_url())
    sync.next()


if __name__ == '__main__':
    from contextlib import suppress
    from sys import argv

    with suppress(KeyboardInterrupt):
        print()
        run(argv[1:])

