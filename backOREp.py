import argparse
import logging
import tarfile
import time
from contextlib import contextmanager
from datetime import datetime

import rcon

from config import SERVERS, DESTINATION, RCON_PASS

_LOGGER = logging.getLogger()


@contextmanager
def save_off(server):
    with rcon.Client('localhost', SERVERS[server]["rcon"], passwd=RCON_PASS) as client:
        client.run('save-off')
        client.run('save-all')
        time.sleep(2)
        try:
            yield
        finally:
            client.run('save-on')


def is_world(path) -> bool:
    return {"level.dat", "session.lock", "uid.dat"}.issubset(
        child.name for child in path.iterdir() if not child.is_dir()
    )


def is_server(server) -> bool:
    return server in SERVERS


def make_tar(source, output):
    with tarfile.open(output.with_suffix(".tar.gz"), "w:gz") as tar:
        tar.add(source, arcname=source.name)


def simple(server):
    with save_off(server):
        worlds = [
            child
            for child in SERVERS[server]["location"].iterdir()
            if child.is_dir() and is_world(child)
        ]
        for world in worlds:
            source = SERVERS[server]["location"] / world.name
            name = f"{world.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            destination = DESTINATION / server / "simple" / name
            make_tar(source, destination)


def full(server):
    with save_off(server):
        source = SERVERS[server]["location"]
        destination = DESTINATION / server / "full" / datetime.now().strftime('%Y%m%d%H%M%S')
        make_tar(source, destination)


def do_stuff(args):
    types = {
        "full": full,
        "simple": simple
    }
    try:
        for server in args.servers:
            types[args.type](server)
    except KeyError:
        _LOGGER.fatal(f"Invalid backup type {args.type}")
        exit()


def main():
    parser = argparse.ArgumentParser("BackOREp")
    parser.add_argument("-v", "--verbose", nargs="?", const=True)
    required_args = parser.add_argument_group("required arguments")
    required_args.add_argument("-s", "--servers", help="The server name to backup.", required=True)
    required_args.add_argument("-t", "--type", help="Type of backup to run (full, simple).", required=True)
    args = parser.parse_args()
    if args.verbose:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        _LOGGER.addHandler(console_handler)
    if any(not is_server(serv) for serv in args.servers):
        _LOGGER.fatal("Invalid server(s) provided!")
        exit()
    do_stuff(args)


if __name__ == "__main__":
    main()
