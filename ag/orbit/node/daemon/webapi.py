#!/usr/bin/env python3
#
# Copyright (C) 2018 Alpha Griffin
# @%@~LICENSE~@%@

from ag.orbit.command import main
from ag.orbit.webapi import Endpoints
from ag.orbit.node.config import get_webapi_interface, get_webapi_port
from ag.orbit.node.db import TokenDB

from flask import Flask, request, abort
import json


class Server():

    def __init__(self, interface, port, daemon=False):
        self.interface = interface
        self.port = port

        self.flask = Flask(__name__)
        self.daemon = daemon

        if daemon:
            self.tokens = None
        else:
            self.tokens = TokenDB()

        self._handler(Endpoints.USER_TOKENS, "get_user_tokens", "address")

    def run(self, quiet=False):
        if quiet:
            self.flask.logger.disabled = True
            import logging
            logging.getLogger('werkzeug').disabled = True

        self.flask.run(host=self.interface, port=self.port, threaded=self.daemon)

        if self.tokens:
            self.tokens.close()

    def _handler(self, endpoint, fn_name, *args):
        def handler():
            qargs = []
            for name in args:
                val = request.args.get(name)
                if not val: abort(400)
                qargs.append(val)

            tokens = self.tokens if self.tokens else TokenDB()
            try:
                fn = getattr(tokens, fn_name)
                return json.dumps({ endpoint: fn(*qargs) })

            finally:
                if not self.tokens:
                    tokens.close()

        self.flask.add_url_rule("/" + endpoint, view_func=handler)


def run(args):
    if args:
        raise ValueError("Not expecting any arguments")

    print()
    print("Starting server to handle web requests...")

    server()

def server(daemon=False, quiet=False):
    server = Server(get_webapi_interface(), get_webapi_port(), daemon)
    server.run(quiet)


if __name__ == '__main__':
    main(run)

