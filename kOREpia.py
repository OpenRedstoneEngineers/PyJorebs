#!/usr/bin/env python3
import argparse
import asyncio
import logging
import subprocess
import sys

from config import SERVERS, DESTINATION, KOPIA_PASS, SERVERS_LOCATION
from restOREt import shutdown

_NAME = "kOREpia"
_LOGGER = logging.getLogger(_NAME)
_LOGGER.setLevel(logging.DEBUG)


async def run_command(server, command: list, delay: int = 1):
    try:
        _LOGGER.debug(f"({server}) Running command `{' '.join(command)}`")
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=True)
        for line in result.stdout.splitlines():
            _LOGGER.debug(line.rstrip())
    except subprocess.CalledProcessError as e:
        _LOGGER.error(e.output)
    await asyncio.sleep(delay)


async def sequence(server, port):
    _LOGGER.info(f"({server}) Beginning shutdown sequence")
    await shutdown(server, port, _LOGGER)
    await asyncio.sleep(1)
    _LOGGER.info(f"({server}) Stopping")
    await run_command(server, ["/usr/bin/systemctl", "stop", "--user", f"ore@{server}"])
    _LOGGER.info(f"({server}) Backing up")
    await run_command(server, ["kopia", "repository", "connect", "filesystem", "--path",
                         str(DESTINATION / "kopia"), f"--password={KOPIA_PASS}"])
    await run_command(server, ["kopia", "snapshot", "create", str(SERVERS_LOCATION / server)])
    await run_command(server, ["kopia", "repository", "disconnect"])
    _LOGGER.info(f"({server}) Starting")
    await run_command(server, ["/usr/bin/systemctl", "start", "--user", f"ore@{server}"])


async def main():
    parser = argparse.ArgumentParser(_NAME)
    parser.add_argument("-v", "--verbose", nargs="?", const=True)
    required_args = parser.add_argument_group("required arguments")
    required_args.add_argument(
        "-s", "--servers", help="The server name to backup.", nargs="+", choices=SERVERS,
        required=True)
    args = parser.parse_args()
    if args.verbose:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter('[%(asctime)s] %(name)s - %(levelname)s: %(message)s'))
        _LOGGER.addHandler(console_handler)

    info = [(server, SERVERS[server]['ports']['rcon']) for server in args.servers]
    for server, port in sorted(info, key=lambda x: x[1], reverse=True):
        await sequence(server, port)


if __name__ == "__main__":
    asyncio.run(main())
