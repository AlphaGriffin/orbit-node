#!/usr/bin/env python3
#
# Copyright (C) 2018 Alpha Griffin
# @%@~LICENSE~@%@

from ag.orbit import API
from ag.orbit.node.config import get_rpc_url
from ag.orbit.node.db import SyncDB

from bitcoinrpc.authproxy import AuthServiceProxy


def run(args):
    if args is not None and len(args) > 0:
        raise ValueError("Not expecting any arguments")

    api = API()

    print()
    print("Collecting node information...")
    print()
    print("    ORBIT genesis block: {}".format(api.genesis))

    try:
        rpc = AuthServiceProxy(get_rpc_url())
    except TypeError:
        raise ValueError('Not a valid RPC URL. Set a valid RPC URL with: `orbit-node rpc`')

    print()
    print('BCH node')
    info = rpc.getblockchaininfo()

    known = info['headers']
    print("    Last known block: {}".format(known))

    completed = info['blocks']
    print("    Last completed block: {}".format(completed))

    diff = known - completed
    print("    Blocks to complete: {}".format(diff))

    pruned = info['pruned']
    print("    Pruned? {}".format(pruned))

    if pruned:
        prune = info['pruneheight']
        print("    Pruned at block: {}".format(prune))

    print()
    print('ORBIT node database')
    sync = SyncDB()

    last = sync.get_last_block()
    print('    Last block sync: {}'.format(last))

    if not last:
        last = api.genesis - 1

    diff = completed - last
    print('    Blocks to sync: {}'.format(diff))


if __name__ == '__main__':
    from contextlib import suppress
    from sys import argv

    with suppress(KeyboardInterrupt):
        print()
        run(argv[1:])

