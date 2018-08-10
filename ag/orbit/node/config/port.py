#!/usr/bin/env python3
#
# Copyright (C) 2018 Alpha Griffin
# @%@~LICENSE~@%@

from ag.orbit.command import main
from ag.orbit.node.config import get_webapi_port, set_webapi_port


def run(args):
    if args and len(args) != 1:
        raise ValueError("Expecting exactly 1 argument")

    if args:
        port = args[0]

        print()
        print("    Setting web API bind port number to: {}".format(port))

        webapi = set_webapi_port(port)

        print()
        print("Web API bind port saved to: {}".format(webapi))

    else:
        port = get_webapi_port()

        print()
        print("    Bind port number for web API: {}".format(port))


if __name__ == '__main__':
    main(run)

