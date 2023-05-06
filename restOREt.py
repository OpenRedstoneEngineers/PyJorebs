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


async def send(delay, rcon_port, command):
    _LOGGER.info(f"Running command \"{command}\" against \"{rcon_port}\" after {delay} seconds")
    await asyncio.sleep(delay)
    rcOREn.run(rcon_port, command)
    _LOGGER.info(f"Ran \"{command}\" against \"{rcon_port}\"")


def duplicate_first(iterable):
    from itertools import chain
    it = iter(iterable)
    x = next(it)
    return chain((x, x), it)


def restoret_times():
    times_offsetted = duplicate_first(restoret_schedule.keys())
    for (timeout, statement), prev_timeout in zip(restoret_schedule.items(), times_offsetted):
        yield prev_timeout - timeout, statement


async def restoret(port):
    for delay, statement in restoret_times():
        await send(delay, port, statement)
    return "Restarting..."


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

    rcon_ports = [SERVERS[server]['ports']['rcon'] for server in args.servers]

    for statement in await asyncio.gather(
        *(restoret(port) for port in rcon_ports),
        return_exceptions=True,
    ):
        _LOGGER.info(statement)


if __name__ == "__main__":
    asyncio.run(main())
