#!/usr/bin/env python3
import argparse
import logging
import sys
import time

import mysql.connector
import requests

from config import discourse_url, discourse_api_timeout
from secrets import DISCOURSE_TOKEN, MYSQL_PASS

_NAME = "discOREse_sync"
_LOGGER = logging.getLogger(_NAME)
_LOGGER.setLevel(logging.DEBUG)

_DISCOURSE_HEADERS = {
    "Api-Username": "system",
    "Api-Key": DISCOURSE_TOKEN
}


def fetch_discourse_groups():
    form_data = {
        "limit": "ALL"
    }
    resp = requests.post(f"{discourse_url}/admin/plugins/explorer/queries/6/run", headers=_DISCOURSE_HEADERS,
                         data=form_data)
    data = resp.json()['rows']
    return {row[1]: row[0] for row in data}


def fetch_discourse_users():
    form_data = {
        "limit": "ALL"
    }
    resp = requests.post(f"{discourse_url}/admin/plugins/explorer/queries/2/run", headers=_DISCOURSE_HEADERS,
                         data=form_data)
    data = resp.json()['rows']
    return [
        {
            "username": row[0],
            "discourse_id": int(row[1]),
            "discord_id": int(row[2]),
            "mojang_name": None if row[3] == '' else row[3],
            "mojang_uuid": None if row[4] == '' else row[4],
            "groups": row[5],
            "group_ids": row[6]
        }
        for row in data
    ]


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


def update_mojang_data(username, mojang_uuid, mojang_name):
    resp = requests.put(f"{discourse_url}/u/{username}.json", headers=_DISCOURSE_HEADERS,
                        data={"user_fields[2]": mojang_name, "user_fields[3]": mojang_uuid})
    time.sleep(discourse_api_timeout)
    resp.raise_for_status()


def add_discourse_group(user_id, group_id):
    resp = requests.post(f"{discourse_url}/admin/users/{user_id}/groups", headers=_DISCOURSE_HEADERS,
                         data={"group_id": group_id})
    time.sleep(discourse_api_timeout)
    resp.raise_for_status()


def remove_discourse_group(user_id, group_id):
    resp = requests.delete(f"{discourse_url}/admin/users/{user_id}/groups/{group_id}", headers=_DISCOURSE_HEADERS)
    time.sleep(discourse_api_timeout)
    resp.raise_for_status()


def _run():
    _LOGGER.info("Fetching discourse users")
    discourse_users = fetch_discourse_users()
    _LOGGER.info("Fetching discourse groups")
    discourse_groups = fetch_discourse_groups()
    _LOGGER.info("Fetching luckperms and linked users")
    lp_linked_users = fetch_lp_users()
    _LOGGER.info("Iterating through discourse users")
    for user in discourse_users:
        try:
            luckperm_data = lp_linked_users[user["discord_id"]]
        except KeyError:
            _LOGGER.info(f"User {user['username']} not linked via {user['discord_id']}")
            continue
        try:
            user_groups = user["groups"].split(",")
        except AttributeError:
            user_groups = []
        changes_made = False
        if user["mojang_name"] != luckperm_data["ign"] or user["mojang_uuid"] != luckperm_data["uuid"]:
            # If either IGN or UUID is not the same, update discourse, as both can be set with one endpoint
            _LOGGER.info(f"Updating user {user['username']} ({user['discourse_id']}) with {luckperm_data['ign']} "
                         f"({luckperm_data['uuid']})")
            update_mojang_data(user["username"], luckperm_data["uuid"], luckperm_data["ign"])
            changes_made = True
        luckperms_group = luckperm_data['primary_group'].title()
        if luckperms_group == "Default":
            # The "Visitor" group is actually the default group, as that is the default group in luckperms upon join.
            luckperms_group = "Visitor"
        remove_groups = set(user_groups) - {luckperms_group}
        for remove_group in remove_groups:
            # If there are groups the person is in on Discourse but not ingame, remove them.
            _LOGGER.info(f"Removing user {user['username']} ({user['discourse_id']}) from {remove_group}")
            remove_discourse_group(user['discourse_id'], discourse_groups[remove_group])
            changes_made = True
        add_groups = {luckperms_group} - set(user_groups)
        for add_group in add_groups:
            # If there are groups the person is in ingame but not on Discourse, add them.
            _LOGGER.info(f"Adding user {user['username']} ({user['discourse_id']}) to {add_group}")
            try:
                add_discourse_group(user['discourse_id'], discourse_groups[add_group])
            except KeyError:
                _LOGGER.info(f"Could not add to group, likely due to group not existing")
            changes_made = True
        if not changes_made:
            _LOGGER.info(f"No changes necessary for {user['username']} ({user['discourse_id']}) "
                         f"({luckperm_data['ign']}: {luckperm_data['uuid']})")


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
