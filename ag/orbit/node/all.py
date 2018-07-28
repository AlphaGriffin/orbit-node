#!/usr/bin/env python3
#
# Copyright (C) 2018 Alpha Griffin
# @%@~LICENSE~@%@

from ag.orbit.node.config import get_rpc_url
from ag.orbit.node.sync import Process


def run(args):
    if args is not None and len(args) > 0:
        raise ValueError("Not expecting any arguments")

    print('Sync all blocks...')

    print()
    sync = Process(get_rpc_url())
    print()

    while True:
        last = sync.next()

        if last is None:
            print()
            if not sync.refresh():
                break
            print()

    print()
    print('Sync complete')


if __name__ == '__main__':
    from contextlib import suppress
    from sys import argv

    with suppress(KeyboardInterrupt):
        print()
        run(argv[1:])

