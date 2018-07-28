# Copyright (C) 2018 Alpha Griffin
# @%@~LICENSE~@%@


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

from sys import argv, exit
from contextlib import suppress

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
        if args is None or len(args) != 1:
            print()
            print("{} {}: Expecting exactly 1 argument".format(CALL, cmd))
            exit(2)

        from .config import set_rpc_url
        print()
        set_rpc_url(args[0])

    elif cmd == 'info':
        if args is not None:
            print()
            print("{} {}: Not expecting any arguments".format(CALL, cmd))
            exit(3)

        from .info import run
        print()
        try:
            run(args)
        except ValueError as e:
            print()
            print('{} {}: {}'.format(CALL, cmd, e))
            exit(3)

    elif cmd == 'next':
        if args is not None:
            print()
            print("{} {}: Not expecting any arguments".format(CALL, cmd))
            exit(4)

        from .next import run
        print()
        try:
            run(args)
        except ValueError as e:
            print()
            print('{} {}: {}'.format(CALL, cmd, e))
            exit(4)

    elif cmd == 'all':
        if args is not None:
            print()
            print("{} {}: Not expecting any arguments".format(CALL, cmd))
            exit(5)

        from .all import run
        print()
        try:
            run(args)
        except ValueError as e:
            print()
            print('{} {}: {}'.format(CALL, cmd, e))
            exit(5)


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

