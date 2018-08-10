#!/usr/bin/env python3
#
# Copyright (C) 2018 Alpha Griffin
# @%@~LICENSE~@%@

from ag.orbit.command import main
from ag.orbit.node.config import get_webapi_interface, set_webapi_interface


def run(args):
    if args and len(args) != 1:
        raise ValueError("Expecting exactly 1 argument")

    if args:
        ip = args[0]

        print()
        print("    Setting web API bind interface IP to: {}".format(ip))

        webapi = set_webapi_interface(ip)

        print()
        print("Web API bind IP saved to: {}".format(webapi))

    else:
        ip = get_webapi_interface()

        print()
        print("    Bind interface IP for web API: {}".format(ip))


if __name__ == '__main__':
    main(run)

