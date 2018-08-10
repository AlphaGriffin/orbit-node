# Copyright (C) 2018 Alpha Griffin
# @%@~LICENSE~@%@

from ...command import invoke

from sys import argv, exit
from contextlib import suppress


CALL = 'orbit-node config'

def usage():
    print()
    print("Usage: {} <command>".format(CALL))
    print()
    print("    Configuration options.")
    print()
    print("Where <command> is:")
    print("    help             - Display this usage screen")
    print("    rpc [<url>]      - Set or display the BCH node RPC URL")
    print("    interface [<ip>] - Set or display the interface IP to bind to")
    print("    port [<port>]    - Set or display the port number to bind to")
    print()


with suppress(KeyboardInterrupt):
    if len(argv) > 1 and argv[1] is None:
        # we were called from the parent module
        args = argv[2:]
    else:
        args = argv[1:]

    if len(args) < 1:
        usage()
        exit(101)

    cmd = args[0]
    args = args[1:] if len(args) > 1 else None

    if cmd == 'help':
        usage()

    elif cmd == 'rpc':
        from .rpc import run
        invoke(CALL, cmd, 102, run, args, 1, 1, optional=True)

    elif cmd == 'interface':
        from .interface import run
        invoke(CALL, cmd, 103, run, args, 1, 1, optional=True)

    elif cmd == 'port':
        from .port import run
        invoke(CALL, cmd, 103, run, args, 1, 1, optional=True)

    else:
        print()
        print("{}: unknown command: {}".format(CALL, cmd))
        usage()
        exit(199)

