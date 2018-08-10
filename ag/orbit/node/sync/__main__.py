# Copyright (C) 2018 Alpha Griffin
# @%@~LICENSE~@%@

from ...command import invoke

from sys import argv, exit
from contextlib import suppress


CALL = 'orbit-node sync'

def usage():
    print()
    print("Usage: {} <command>".format(CALL))
    print()
    print("    Blockchain synchronization and validation commands.")
    print()
    print("Where <command> is:")
    print("    help         - Display this usage screen")
    print("    info         - Print information about the node status")
    print("    next         - Process next block, if available")
    print("    all          - Process all available blocks")
    print()


with suppress(KeyboardInterrupt):
    if len(argv) > 1 and argv[1] is None:
        # we were called from the parent module
        args = argv[2:]
    else:
        args = argv[1:]

    if len(args) < 1:
        usage()
        exit(201)

    cmd = args[0]
    args = args[1:] if len(args) > 1 else None

    if cmd == 'help':
        usage()

    elif cmd == 'info':
        from .info import run
        invoke(CALL, cmd, 202, run, args)

    elif cmd == 'next':
        from .next import run
        invoke(CALL, cmd, 203, run, args)

    elif cmd == 'all':
        from .all import run
        invoke(CALL, cmd, 204, run, args)

    else:
        print()
        print("{}: unknown command: {}".format(CALL, cmd))
        usage()
        exit(299)

