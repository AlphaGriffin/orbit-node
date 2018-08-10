# Copyright (C) 2018 Alpha Griffin
# @%@~LICENSE~@%@

#import ag.logging as log

from os import makedirs, path

from appdirs import AppDirs
dirs = AppDirs("orbit-node", "Alpha Griffin")

dir = dirs.user_config_dir
#log.debug("Starting up", configdir=dir)

if not path.exists(dir):
    #log.info("Running first-time setup for configuration...")

    #log.debug("Creating user config directory")
    makedirs(dir, exist_ok=True)

if not path.isdir(dir):
    #log.fatal("Expected a directory for configdir", configdir=dir)
    raise Exception("Not a directory: " + dir)


def get_rpc_url():
    rpc = path.join(dir, 'rpc')

    if not path.exists(rpc):
        raise ValueError('RPC URL not set. You must set a URL first with: `orbit-node config rpc`')

    with open(rpc, 'r') as rpcin:
        return rpcin.readline()

def set_rpc_url(url):
    rpc = path.join(dir, 'rpc')
    with open(rpc, 'w') as out:
        out.write(url)

    return rpc


def get_webapi_interface():
    webapi = path.join(dir, 'webapi_interface')

    if not path.exists(webapi):
        return '127.0.0.1'

    with open(webapi, 'r') as webapiin:
        return webapiin.readline()

def set_webapi_interface(interface):
    webapi = path.join(dir, 'webapi_interface')
    with open(webapi, 'w') as out:
        out.write(interface)

    return webapi


def get_webapi_port():
    webapi = path.join(dir, 'webapi_port')

    if not path.exists(webapi):
        from ag.orbit.webapi import DEFAULT_PORT
        return DEFAULT_PORT

    with open(webapi, 'r') as webapiin:
        return int(webapiin.readline())

def set_webapi_port(port):
    if int(port) < 1:
        raise ValueError("Port number must be a positive integer.")

    webapi = path.join(dir, 'webapi_port')
    with open(webapi, 'w') as out:
        out.write(port)

    return webapi

