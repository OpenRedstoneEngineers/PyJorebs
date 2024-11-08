#!/usr/bin/env python3.10
import argparse
import csv
import logging
import sys

import mysql.connector
import requests

from config import discourse_url, APPS_LOCATION, MYSQL_PASS, DISCOURSE_TOKEN

_NAME = "fOREtch_apps"
_LOGGER = logging.getLogger(_NAME)
_LOGGER.setLevel(logging.DEBUG)

_DISCOURSE_HEADERS = {
    "Api-Username": "system",
    "Api-Key": DISCOURSE_TOKEN
}


def fetch_accepted_apps():
    form_data = {
        "limit": "ALL"
    }
    resp = requests.post(f"{discourse_url}/admin/plugins/explorer/queries/14/run", headers=_DISCOURSE_HEADERS,
                         data=form_data)
    data = resp.json()['rows']
    return [row for row in data]


def fetch_lp_users():
    with mysql.connector.connect(host="localhost", user="mcadmin", password=MYSQL_PASS) as conn:
        cursor = conn.cursor()
        query = """SELECT uuid, ign, (UPPER(ign) != UPPER(username)) as ign_flag, discord_id, primary_group
                    FROM network_link.nu_users
                    JOIN ore_luckperms.luckperms_players on m_uuid = uuid
                    WHERE discord_id IS NOT NULL;"""
        cursor.execute(query)
        results = cursor.fetchall()
        return {
            int(row[3]): {
                "uuid": row[0],
                "ign": row[1],
                "ign_flag": row[2],
                "primary_group": row[4]
            }
            for row in results
        }


def _run():
    _LOGGER.info("Fetching discourse accepted apps")
    discourse_apps = fetch_accepted_apps()
    _LOGGER.info("Fetching luckperms and linked users")
    lp_linked_users = fetch_lp_users()
    _LOGGER.info("Iterating through apps")
    export_data = [["Created At", "URL", "Discord ID", "UUID", "IGN", "Primary Group"]]
    for app in discourse_apps:
        export_row = [app[1], app[0], app[3]]
        try:
            linked_user = lp_linked_users[int(app[3])]
            export_row.extend([linked_user['uuid'], linked_user['ign'], linked_user['primary_group']])
        except (KeyError, TypeError):
            export_row.extend(["no link?", '', ''])
        _LOGGER.debug(f"Adding {export_row} to export")
        export_data.append(export_row)
    with open(str(APPS_LOCATION), "w", newline="") as output:
        writer = csv.writer(output)
        writer.writerows(export_data)


def main():
    parser = argparse.ArgumentParser(_NAME)
    parser.add_argument("-v", "--verbose", nargs="?", const=True)
    args = parser.parse_args()
    if args.verbose:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter('[%(asctime)s] %(name)s - %(levelname)s: %(message)s'))
        _LOGGER.addHandler(console_handler)

    _run()


if __name__ == "__main__":
    main()
