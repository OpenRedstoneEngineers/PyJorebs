from pathlib import Path


common_mount = ("/home/mcadmin/prod/common", "/common")


paper_mounts = [
    ("/home/mcadmin/prod/{server}", "/data"),
    common_mount,
]


dynmap_mount = ("/store/tiles/{server}", "/data/plugins/dynmap/web/tiles")


memory_opts = "-Xms{memory} -Xmx{memory}"
paper_command = f"cd /data && exec java {memory_opts} -jar /common/paper.jar"
waterfall_command = "cd /data && exec java {memory_opts} -jar /common/waterfall.jar"


SERVERS = {
    "build": {
        "ports": {
            "rcon": 1234,
            "dynmap": 2321,
            "game": 1255,
        },
        "public": {"dynmap", "game"},
        "extra": {
            "memory": "8G",
        },
        "run_command": paper_command,
        "mounts": [*paper_mounts, dynmap_mount],
    },
    "school": {
        "ports": {
            "rcon": 1234,
            "dynmap": 2321,
            "game": 1255,
        },
        "public": {"dynmap", "game"},
        "extra": {
            "memory": "4G",
        },
        "run_command": paper_command,
        "mounts": [*paper_mounts, dynmap_mount],
    },
    "prodxy": {
        "ports": {
            "game": 3233,
        },
        "public": {"game"},
        "extra": {
            "memory": "1G",
        },
        "run_command": waterfall_command,
        "mounts": [common_mount],
    }
}


PODMAN_IMAGE_NAME = "docker.io/library/openjdk:16.0.1-slim"

RCON_PASS = "passwOREd"
SERVERS_LOCATION = Path("/home/mcadmin/mcservers")
DESTINATION = Path("/home/mcadmin/backups")
