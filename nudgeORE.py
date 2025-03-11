#!/usr/bin/env python3
import argparse
import logging
import sys

import requests
import time

from config import NUDGEORE_HOURS, NUDGEORE_WEBHOOK, DISCORD_LIMIT, NUDGEORE_RATELIMIT, get_discourse_url, NUDGEORE_LINKS


_NAME = "nudgeORE"
_LOGGER = logging.getLogger(_NAME)
_LOGGER.setLevel(logging.DEBUG)


def get_forum_title(url) -> str:
    return url.split("/")[-2].replace("-", " ").title()


def hours_since(date_string: str, hours) -> bool:
    # this is always Tru? xd
    return True


def parse_forum(forum: dict):
    for topic in forum["topic_list"]["topics"]:
        if not hours_since(topic["last_posted_at"], NUDGEORE_HOURS): continue

        most_recent_poster = [poster for poster in topic["posters"] if "Most Recent Poster" in poster["description"]][0]
        last_poster = [user for user in forum["users"] if user["id"] == most_recent_poster["user_id"]][0]

        if last_poster.get("admin", False) or last_poster.get("moderator", False): continue

        if topic["closed"] or topic["archived"]:
            continue

        yield {"id": topic["id"], "title": topic["title"], "url": get_discourse_url(f"t/{topic['slug']}/{topic['id']}")}


def post_to_discord(posts: list, title: str) -> bool:
    if not NUDGEORE_WEBHOOK:
        _LOGGER.error("NudgeORE: Discord webhook URL is not set")
        return False

    _LOGGER.info(f"{len(posts)} posts found for nudging")

    # Prepare separate messages under 2000 characters
    messages = []
    current_message = ""
    if posts:
        current_message = f"# {title}\n"

    for post in posts:
        entry = f"* New action required: [{post['title']}]({post['url']})\n"
        if len(current_message) + len(entry) <= DISCORD_LIMIT:
            current_message += entry
        else:
            if current_message:
                messages.append(current_message)
            # Start a new message
            current_message = f"# {title}\n"
            if len(entry) <= DISCORD_LIMIT:
                current_message += entry
            else:
                _LOGGER.error(f"Skipped entry: {post['title']} (exceeds character limit)")

    if current_message:
        messages.append(current_message)

    success = True
    for message in messages:
        data = {"content": message}
        if not _post_webhook(data):
            success = False

    return success


def _post_webhook(data):
    retries = 3
    for i in range(retries):
        response = requests.post(NUDGEORE_WEBHOOK, json=data)
        if response.status_code == 204:
            _LOGGER.info("Message sent successfully")
            return True
        else:
            _LOGGER.error(f"Failed to send message. Status code: {response.status_code}. Retrying...")
            _LOGGER.error(f"Response content: {response.text}")
            time.sleep(NUDGEORE_RATELIMIT)
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", nargs="?", const=True)
    args = parser.parse_args()
    if args.verbose:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter('[%(asctime)s] %(name)s - %(levelname)s: %(message)s'))
        _LOGGER.addHandler(console_handler)

    for link in NUDGEORE_LINKS:
        parsed = requests.get(link).json()
        output = [entry for entry in parse_forum(parsed)]
        post_to_discord(output, get_forum_title(link))
        time.sleep(NUDGEORE_RATELIMIT)


if __name__ == "__main__":
    main()
