import argparse
import logging
import tarfile
import time
from contextlib import contextmanager
from datetime import datetime

import rcon

from config import SERVERS, DESTINATION, RCON_PASS, SERVERS_LOCATION

_LOGGER = logging.getLogger()


@contextmanager
def save_off(server):
    with rcon.Client('localhost', server["rcon"], passwd=RCON_PASS) as client:
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


def make_tar(source, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output.with_suffix(".tar.gz"), "w:gz") as tar:
        tar.add(source, arcname=source.name)


def simple(server):
    with save_off(server):
        worlds = [
            child
            for child in server["location"].iterdir()
            if child.is_dir() and is_world(child)
        ]
        for world in worlds:
            source = server["location"] / world.name
            name = f"{world.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            destination = DESTINATION / server["name"] / "simple" / name
            make_tar(source, destination)


def full(server):
    with save_off(server):
        source = server["location"]
        destination = DESTINATION / server["name"] / "full" / datetime.now().strftime('%Y%m%d%H%M%S')
        make_tar(source, destination)


backup_types = {
    "full": full,
    "simple": simple,
}


def main():
    parser = argparse.ArgumentParser("BackOREp")
    parser.add_argument("-v", "--verbose", nargs="?", const=True)
    required_args = parser.add_argument_group("required arguments")
    required_args.add_argument(
        "-s", "--servers", help="The server name to backup.", nargs="+", choices=SERVERS,
        required=True)
    required_args.add_argument("-t", "--type", help=f"Type of backup to run.", choices=backup_types, required=True)
    args = parser.parse_args()
    if args.verbose:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        _LOGGER.addHandler(console_handler)

    for server in args.servers:
        backup_types[args.type]({
            **SERVERS[server],
            "name": server,
            "location": SERVERS_LOCATION / server
        })


if __name__ == "__main__":
    main()
