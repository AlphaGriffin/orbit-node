#!/usr/bin/env python3
#
# Copyright (C) 2018 Alpha Griffin
# @%@~LICENSE~@%@

from ag.orbit.command import main, read_char
from ag.orbit.node.daemon.sync import start, forever
from ag.orbit.node.daemon.webapi import server

from threading import Thread, Event
from sys import stdin, stdout


def run(args):
    if args:
        raise ValueError("Not expecting any arguments")

    print()
    print("Starting Web API daemon...")
    webapi = Thread(name="daemon-webapi", target=server, args=(True, True), daemon=True)
    webapi.start()
    print("Daemon running")

    start()


if __name__ == '__main__':
    main(run)

