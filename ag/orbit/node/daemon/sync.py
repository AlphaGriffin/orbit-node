#!/usr/bin/env python3
#
# Copyright (C) 2018 Alpha Griffin
# @%@~LICENSE~@%@

from ag.orbit.command import main, read_char
from ag.orbit.node.config import get_rpc_url
from ag.orbit.node.sync import Process

from threading import Thread, Event
from sys import stdin, stdout


quit = None
sleep = None

def run(args):
    global quit, sleep

    if args:
        raise ValueError("Not expecting any arguments")

    start()

def start():
    global quit, sleep

    print()
    print("Starting sync daemon...")

    quit = False
    sleep = Event()

    daemon = Thread(name="daemon-sync", target=forever, daemon=True)
    daemon.start()

    print("Daemon running")

    if stdin.isatty() and stdout.isatty():
        print()

        while not quit:
            print(">>> Hit [I] for info, [Q] to quit after current block, or [^C] to exit immediately <<<")

            c = read_char()

            if 'q' == c or 'Q' == c:
                quit = True
                sleep.set()
                daemon.join()

            elif 'i' == c or 'I' == c:
                print()
                sync = Process(url=get_rpc_url())
                sync.get_info()
                print()

            elif '\x03' == c:
                print()
                print("Interrupted")
                raise KeyboardInterrupt()

            #else:
            #    print(repr(c))

        print()
        print("User quit")

    else:
        daemon.join()

def forever():
    sync = Process(url=get_rpc_url(), out=None)

    while not quit:
        last = sync.next()

        if last is None:
            if not sync.refresh():
                # wait 10 seconds between block checks
                sleep.wait(10)


if __name__ == '__main__':
    main(run)

