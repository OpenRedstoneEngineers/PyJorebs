#!/usr/bin/env python3
import argparse
import logging
import subprocess
import sys
import time
from datetime import datetime

from config import DESTINATION, MYSQL_PASS
from util import make_tar

_NAME = "dOREmp"
_LOGGER = logging.getLogger(_NAME)
_LOGGER.setLevel(logging.DEBUG)


def doremp(user, password):
    doremp_location = DESTINATION / "databases" / f"databases_{datetime.now().strftime('%Y%m%d%H%M%S')}.sql"
    _LOGGER.info("Initiating dump")
    command = f"podman exec mariadb mysqldump --hex-blob --all-databases -u{user} -p{password}".split(" ")
    sub = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = sub.communicate()
    if sub.returncode == 0:
        _LOGGER.info("Generating dump")
        time.sleep(2)  # This is an ugly hack
        doremp_location.write_bytes(output)
        time.sleep(2)  # Dont tell Pauk
        _LOGGER.info("Compressing dump")
        make_tar(doremp_location, doremp_location.parent)
    else:
        _LOGGER.error(error)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", nargs="?", const=True)
    args = parser.parse_args()
    if args.verbose:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter('[%(asctime)s] %(name)s - %(levelname)s: %(message)s'))
        _LOGGER.addHandler(console_handler)

    doremp("mcadmin", MYSQL_PASS)


if __name__ == "__main__":
    main()
