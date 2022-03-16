#!/usr/bin/env python3
import argparse
import logging
import sys
import time
from contextlib import contextmanager
from datetime import datetime

import rcon

from config import SERVERS, DESTINATION, SERVERS_LOCATION, secrets
from util import make_tar

_NAME = "BackOREp"
_LOGGER = logging.getLogger(_NAME)
_LOGGER.setLevel(logging.DEBUG)


@contextmanager
def save_off(server):
    try:
        with rcon.Client('localhost', server["ports"]["rcon"], passwd=secrets.RCON_PASS) as client:
            _LOGGER.debug(f"Running 'save-off', 'save-all' for {server['name']}")
            client.run('save-off')
            client.run('save-all')
            time.sleep(2)
            try:
                yield
            finally:
                _LOGGER.debug(f"Running 'save-on' for {server['name']}")
                client.run('save-on')
    except ConnectionError:
        _LOGGER.warning(f"Unable to connect to rcon for {server['name']}, continuing to save")
        yield


def is_world(path) -> bool:
    return {"level.dat", "session.lock", "uid.dat"}.issubset(
        child.name for child in path.iterdir() if not child.is_dir()
    )


def simple(server):
    _LOGGER.debug(f"Performing simple backup of server {server['name']}")
    with save_off(server):
        worlds = [
            child
            for child in server["location"].iterdir()
            if child.is_dir() and is_world(child)
        ]
        _LOGGER.debug(f"Found worlds {worlds}")
        for world in worlds:
            source = server["location"] / world.name
            name = f"{world.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            destination = DESTINATION / server["name"] / "simple" / name
            _LOGGER.debug(f"Generating tar {destination} from {source}")
            make_tar(source, destination)


def full(server):
    _LOGGER.debug(f"Performing full backup of server {server['name']}")
    with save_off(server):
        source = server["location"]
        destination = DESTINATION / server["name"] / "full" / datetime.now().strftime('%Y%m%d%H%M%S')
        _LOGGER.debug(f"Generating tar {destination} from {source}")
        make_tar(source, destination)


def main():
    backup_types = {
        "full": full,
        "simple": simple,
    }
    parser = argparse.ArgumentParser(_NAME)
    parser.add_argument("-v", "--verbose", nargs="?", const=True)
    required_args = parser.add_argument_group("required arguments")
    required_args.add_argument(
        "-s", "--servers", help="The server name to backup.", nargs="+", choices=SERVERS,
        required=True)
    required_args.add_argument("-t", "--type", help=f"Type of backup to run.", choices=backup_types, required=True)
    args = parser.parse_args()
    if args.verbose:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter('[%(asctime)s] %(name)s - %(levelname)s: %(message)s'))
        _LOGGER.addHandler(console_handler)

    for server in args.servers:
        backup_types[args.type]({
            **SERVERS[server],
            "name": server,
            "location": SERVERS_LOCATION / server
        })


if __name__ == "__main__":
    main()
