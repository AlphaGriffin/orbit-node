# Copyright (C) 2018 Alpha Griffin
# @%@~LICENSE~@%@

def usage():
    print()
    print("Usage: orbit-node <command>")
    print()
    print("Where <command> is:")
    print("   help      - Display this usage screen")
    print()

from sys import argv, exit

if len(argv) < 2:
    usage()
    exit(1)
    
elif argv[1] == 'help':
    usage()

else:
    print("orbit-node: unknown command: " + argv[1])
    usage()
    exit(2)

