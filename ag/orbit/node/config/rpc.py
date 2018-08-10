#!/usr/bin/env python3
#
# Copyright (C) 2018 Alpha Griffin
# @%@~LICENSE~@%@

from ag.orbit.command import main
from ag.orbit.node.config import get_rpc_url, set_rpc_url


def run(args):
    if args and len(args) != 1:
        raise ValueError("Expecting exactly 1 argument")

    if args:
        url = args[0]

        print()
        print("    Setting bitcoind RPC URL to: {}".format(url))

        rpc = set_rpc_url(url)

        print()
        print("RPC URL saved to: {}".format(rpc))

    else:
        url = get_rpc_url()

        print()
        print("    RPC URL for bitcoind: {}".format(url))


if __name__ == '__main__':
    main(run)

