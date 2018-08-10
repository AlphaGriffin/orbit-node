# Copyright (C) 2018 Alpha Griffin
# @%@~LICENSE~@%@

from sys import argv, exit
from contextlib import suppress


CALL = 'orbit-node'

def usage():
    print()
    print("Usage: {} <module>".format(CALL))
    print()
    print("    ORBIT validating node for tokens on Bitcoin Cash.")
    print()
    print("Where <module> is:")
    print("    help         - Display this usage screen")
    print("    config       - Configuration options")
    print("    sync         - Blockchain synchronization and validation commands")
    print("    daemon       - Web API and continuous operation commands")
    print()


with suppress(KeyboardInterrupt):
    args = argv[1:]

    if len(args) < 1:
        usage()
        exit(1)

    argv[1] = None # a hack so sub-modules can tell if they were invoked from here, or directly
    module = args[0]
    args = args[1:] if len(args) > 1 else None
        
    if module == 'help':
        usage()

    elif module == 'config':
        from .config import __main__

    elif module == 'sync':
        from .sync import __main__

    elif module == 'daemon':
        from .daemon import __main__

    else:
        print()
        print("{}: unknown module: {}".format(CALL, module))
        usage()
        exit(99)

