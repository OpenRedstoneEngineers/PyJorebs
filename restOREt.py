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


async def send(logger, delay, server, rcon_port, commands):
    await asyncio.sleep(delay)
    for command in commands:
        logger.info(f"({server}) Running command \"{command}\" against \"{rcon_port}\" after {delay} seconds")
        rcOREn.run(rcon_port, command, logger)


async def shutdown(server, port, logger=_LOGGER):
    await asyncio.gather(*[send(logger, delay.seconds, server, port, statements)
                           for delay, statements in sorted(restoret_schedule.items())])


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

    server_info = [(server, SERVERS[server]['ports']['rcon']) for server in args.servers]

    for statement in await asyncio.gather(
        *(shutdown(server, port) for server, port in server_info),
        return_exceptions=True,
    ):
        _LOGGER.info(statement)


if __name__ == "__main__":
    asyncio.run(main())
