#!/usr/bin/env python3
#
# Copyright (C) 2018 Alpha Griffin
# @%@~LICENSE~@%@

from ag.orbit.command import main
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
    main(run)

