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


async def kopia(server):
    await run_command(server, ["kopia", "repository", "connect", "filesystem", "--path",
                               str(DESTINATION / "kopia"), f"--password={KOPIA_PASS}"])
    await run_command(server, ["kopia", "snapshot", "create", str(SERVERS_LOCATION / server)])
    await run_command(server, ["kopia", "repository", "disconnect"])


async def sequence(server, port):
    service_control = True
    if server != "velocity":
        _LOGGER.info(f"({server}) Beginning shutdown sequence")
        try:
            await shutdown(server, port, _LOGGER)
        except ConnectionRefusedError:
            service_control = False
            _LOGGER.warning(f"({server}) Unable to perform shutdown sequence")
    else:
        _LOGGER.info(f"({server}) Skipping shutdown sequence")
    await asyncio.sleep(1)
    if service_control:
        await run_command(server, ["/usr/bin/systemctl", "stop", "--user", f"ore@{server}"])
    try:
        _LOGGER.info(f"({server}) Backing up")
        await kopia(server)
    finally:
        if service_control:
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

    info = [(server, SERVERS[server]['ports'].get('rcon', 0)) for server in args.servers]
    for server, port in sorted(info, key=lambda x: x[1], reverse=True):
        await sequence(server, port)


if __name__ == "__main__":
    asyncio.run(main())
