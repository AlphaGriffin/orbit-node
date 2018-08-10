# Copyright (C) 2018 Alpha Griffin
# @%@~LICENSE~@%@

from ...command import invoke

from sys import argv, exit
from contextlib import suppress


CALL = 'orbit-node daemon'

def usage():
    print()
    print("Usage: {} <command>".format(CALL))
    print()
    print("    Daemon modes for continuous operation.")
    print()
    print("Where <command> is:")
    print("    help         - Display this usage screen")
    print("    sync         - Sync blocks and validate transactions")
    print("    webapi       - Listen for client connections")
    print("    all          - Sync blocks, validate transactions, and listen for client connections")
    print()


with suppress(KeyboardInterrupt):
    if len(argv) > 1 and argv[1] is None:
        # we were called from the parent module
        args = argv[2:]
    else:
        args = argv[1:]

    if len(args) < 1:
        usage()
        exit(301)

    cmd = args[0]
    args = args[1:] if len(args) > 1 else None

    if cmd == 'help':
        usage()

    elif cmd == 'sync':
        from .sync import run
        invoke(CALL, cmd, 302, run, args)

    elif cmd == 'webapi':
        from .webapi import run
        invoke(CALL, cmd, 303, run, args)

    elif cmd == 'all':
        from .all import run
        invoke(CALL, cmd, 304, run, args)

    else:
        print()
        print("{}: unknown command: {}".format(CALL, cmd))
        usage()
        exit(399)

