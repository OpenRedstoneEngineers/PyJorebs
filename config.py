from dotenv import load_dotenv
from os import getenv

from pathlib import Path

from mergedeep import Strategy, merge as do_merge

load_dotenv(Path(__file__).parent / ".env")

RCON_PASS = getenv("RCON_PASS")
MYSQL_PASS = getenv("MYSQL_PASS")
DISCOURSE_TOKEN = getenv("DISCOURSE_TOKEN")
NUDGEORE_WEBHOOK = getenv("NUDGEORE_WEBHOOK")

def merge(*args, **kwargs):
    return do_merge(*args, strategy=Strategy.ADDITIVE, **kwargs)


schemati_mount = ("/home/mcadmin/actual_schematics", "/schematics")
common_mounts = [
    ("/home/mcadmin/prod/{server}", "/data"),
    ("/home/mcadmin/prod/common", "/common"),
    schemati_mount,
]
dynmap_mount = ("/store/tiles/{server}", "/data/plugins/dynmap/web/tiles")

khttp_hack = "--add-opens java.base/java.net=ALL-UNNAMED --add-opens java.base/sun.net.www.protocol.https=ALL-UNNAMED"

memory_opts = "-Xms{memory} -Xmx{memory}"
paper_command = f"cd /data && exec java {khttp_hack} {memory_opts} -jar /common/paper-1.20.4-496.jar" + " {extra_args}"
velocity_command = f"cd /data && exec java {khttp_hack} {memory_opts} -jar " + "/common/velocity-{velocity_version}.jar {extra_args}"
podman_jdk_image = "docker.io/library/openjdk:17.0.2-slim"
temurin_image = "docker.io/library/eclipse-temurin:22-jre-jammy"
discourse_url = "https://discourse.openredstone.org"
# Our discourse instance is self-hosted and our limit was customized to 500/minute
# Despite this, a 0.1 delay is more than reasonable to handle the changes on a daily basis
discourse_api_timeout = 0.1


def title(title_, subtitle):
    return  (f'title @a title {{"text":"{title_}"}}',
             f'title @a subtitle {{"text":"{subtitle}"}}')


restoret_schedule = {
    300: title("Server restart", "5 minutes"),
    60: title("Server restart", "1 minute"),
    20: title("Server restart", "20 seconds"),
    5: title("Server restarting...", ""),
    0: ["stop"],
}


def paper_server(index, memory):
    return {
        "ports": {
            "game": 30000 + index,
            "rcon": 30100 + index,
        },
        "public": {},
        "extra": {
            "memory": memory,
        },
        "image": temurin_image,
        "run_command": paper_command,
        "mounts": [*common_mounts],
    }


SERVERS = {
    "hub": paper_server(index=0, memory="2G"),
    "build": merge(
        paper_server(index=1, memory="12G"),
        {
            "ports": {
                "dynmap": 30201,
                "schemati": 8080,
            },
            "public": {"dynmap"},
            "mounts": [dynmap_mount],
        },
    ),
    "school": paper_server(index=2, memory="4G"),
    "survival": paper_server(index=3, memory="4G"),
    "play": paper_server(index=4, memory="4G"),
    "boat": paper_server(index=5, memory="4G"),
    "competition": paper_server(index=6, memory="8G"),
    "seasonal": paper_server(index=7, memory="4G"),
    "velocity": {
        "ports": {
            "game": 25565
        },
        "public": {"game"},
        "extra": {
            "memory": "1G",
            "velocity_version": "3.3.0-SNAPSHOT-390"
        },
        "image": temurin_image,
        "run_command": velocity_command,
        "mounts": [*common_mounts]
    }
}

SERVICES = {
    **SERVERS,
    "chad": {
        "ports": {},
        "public": {},
        "extra": {},
        "image": podman_jdk_image,
        "run_command": f"cd /data && exec java {khttp_hack} -jar Chad-1.0-all.jar config.yaml",
        "mounts": [("/home/mcadmin/private/chad", "/data")],
    },
    "enginexd": {
        "ports": {
            "http": (42080, 80),
            "https": (42043, 443),
        },
        "public": {"http", "https"},
        "extra": {},
        "image": "docker.io/library/nginx",
        "mounts": [
            ("/store/archive", "/var/www/archive.openredstone.org"),
            ("/home/mcadmin/podshare/nginx", "/etc/nginx/conf.d"),
            ("/home/mcadmin/private/letsencrypt", "/etc/letsencrypt"),
            ("/home/mcadmin/private/wwwcertbot", "/var/www/certbot"),
        ],
    },
    "mchprs": {
        "ports": {
            "game": (42068, 25565),
        },
        "public": {},
        "extra": {},
        "image": "docker.io/stackdoubleflow/mchprs:plot-scale-5",
        "mounts": [
            ("/home/mcadmin/private/mchprs", "/data"),
            ("/home/mcadmin/actual_schematics", "/data/schems"),
        ],
    },
}

SERVERS_LOCATION = Path("/home/mcadmin/prod")
DESTINATION = Path("/store/backups")
APPS_LOCATION = Path("/home/mcadmin/apps/accepted_apps.csv")

NUDGEORE_HOURS = 24
DISCOURSE_URL = "https://discourse.openredstone.org"  # Ends without /
NUDGEORE_RATELIMIT = 5
DISCORD_LIMIT = 2000  # Discord's message character limit

def get_discourse_url(stub) -> str:
    return f"{DISCOURSE_URL}/{stub}"

NUDGEORE_LINKS = (
    get_discourse_url("c/builder-applications/9.json"),
    get_discourse_url("c/engineer-applications/22.json"),
    get_discourse_url("c/moderation/petitions/20.json"),
    get_discourse_url("c/moderation/appeals/31.json"),
    get_discourse_url("c/moderation/suggestions/19.json"),
)
