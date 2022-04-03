#!/usr/bin/env python3
import argparse
import logging
import re
import sys
from typing import List

import rcon

from config import SERVERS, secrets

_NAME = "rcOREn"
_LOGGER = logging.getLogger(_NAME)
_LOGGER.setLevel(logging.DEBUG)


def run(port: int, command: str, logger):
    with rcon.Client('localhost', port, passwd=secrets.RCON_PASS) as client:
        logger.info(f"Port '{port}': running '{command}'")
        response = re.sub(r"""§[0-9a-flmno]""", "", client.run(command))
        logger.info(f"Response:\n{response}")


def _run(rcon_ports: List[int], command: str):
    for port in rcon_ports:
        try:
            run(port, command, _LOGGER)
        except ConnectionRefusedError as e:
            _LOGGER.error(e)


def main():
    parser = argparse.ArgumentParser(_NAME)
    parser.add_argument("-v", "--verbose", nargs="?", const=True)
    required_args = parser.add_argument_group("required arguments")
    required_args.add_argument(
        "-s", "--servers", help="The server name to run command on.", nargs="+", choices=SERVERS,
        required=True)
    required_args.add_argument("-c", "--command", help=f"The command to run.", nargs="+", required=True)
    args = parser.parse_args()
    if args.verbose:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter('[%(asctime)s] %(name)s - %(levelname)s: %(message)s'))
        _LOGGER.addHandler(console_handler)

    _run([SERVERS[server]['ports']['rcon'] for server in args.servers], " ".join(args.command))


if __name__ == "__main__":
    main()
