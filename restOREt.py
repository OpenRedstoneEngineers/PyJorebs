#!/usr/bin/env python3
import argparse
import asyncio
import logging
import sys

import rcOREn
from config import SERVERS, restoret_schedule

_NAME = "restOREt"
_LOGGER = logging.getLogger(_NAME)
_LOGGER.setLevel(logging.DEBUG)


async def send(delay, rcon_ports, command):
    _LOGGER.info(f"Running command \"{command}\" after {delay} seconds")
    await asyncio.sleep(delay)
    await rcOREn.run(rcon_ports, command)
    _LOGGER.info(f"Completing command \"{command}\"")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", nargs="?", const=True)
    required_args = parser.add_argument_group("required arguments")
    required_args.add_argument("-s", "--servers", help="The server name to restart.", nargs="+", choices=SERVERS,
                               required=True)
    args = parser.parse_args()
    if args.verbose:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter('[%(asctime)s] %(name)s - %(levelname)s: %(message)s'))
        _LOGGER.addHandler(console_handler)

    restart_in = next(iter(restoret_schedule.keys()))

    rcon_ports = [SERVERS[server]['ports']['rcon'] for server in args.servers]

    tasks = [
        asyncio.create_task(send(restart_in - timeout, rcon_ports, f'title @a title {{"text":"{statement}"}}'))
        for timeout, statement in restoret_schedule.items()
    ]

    tasks.append(asyncio.create_task(send(restart_in, rcon_ports, "stop")))

    [await task for task in tasks]


if __name__ == "__main__":
    asyncio.run(main())
