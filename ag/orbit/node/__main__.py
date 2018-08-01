# Copyright (C) 2018 Alpha Griffin
# @%@~LICENSE~@%@

from ..command import invoke

from sys import argv, exit
from contextlib import suppress


CALL = 'orbit-node'

def usage():
    print()
    print("Usage: {} <command>".format(CALL))
    print()
    print("Where <command> is:")
    print("   help          - Display this usage screen")
    print("   rpc <url>     - Set url for RPC bitcoind connection to <rpc>")
    print("   info          - Print information about the node status")
    print("   next          - Process next block, if available")
    print("   all           - Process all available blocks")
    #print("   daemon        - Run continuously processing all blocks")
    print()


with suppress(KeyboardInterrupt):
    args = argv[1:]

    if len(args) < 1:
        usage()
        exit(1)

    cmd = args[0]
    args = args[1:] if len(args) > 1 else None
        
    if cmd == 'help':
        usage()

    elif cmd == 'rpc':
        from .config import set_rpc_url
        invoke(CALL, cmd, 2, set_rpc_url, args, 1, 1, True)

    elif cmd == 'info':
        from .info import run
        invoke(CALL, cmd, 3, run, args)

    elif cmd == 'next':
        from .next import run
        invoke(CALL, cmd, 4, run, args)

    elif cmd == 'all':
        from .all import run
        invoke(CALL, cmd, 5, run, args)

    #elif cmd == 'daemon':
    #    if args is not None:
    #        print()
    #        print("{} {}: Not expecting any arguments".format(CALL, cmd))
    #        exit(6)

    else:
        print()
        print("{}: unknown command: {}".format(CALL, cmd))
        usage()
        exit(99)

