try:
    import secrets
except ImportError:
    print("Could not find secrets.py! Using example configuration")
    # TODO: this is probably bad, but it makes the IDE happy
    import secrets_example as secrets

from pathlib import Path


schemati_mount = ("/home/mcadmin/actual_schematics", "/schematics")
common_mounts = [
    ("/home/mcadmin/prod/{server}", "/data"),
    ("/home/mcadmin/prod/common", "/common"),
    schemati_mount,
]
dynmap_mount = ("/store/tiles/{server}", "/data/plugins/dynmap/web/tiles")


memory_opts = "-Xms{memory} -Xmx{memory}"
paper_command = f"cd /data && exec java {memory_opts} -jar /common/paper-1.17.1-398.jar" + " {extra_args}"
waterfall_command = f"cd /data && exec java --add-opens java.base/java.net=ALL-UNNAMED --add-opens java.base/sun.net.www.protocol.https=ALL-UNNAMED {memory_opts} -jar /common/waterfall-1.18-466.jar" + " {extra_args}"
podman_jdk_image = "docker.io/library/openjdk:16.0.2-slim"


SERVERS = {
    "hub": {
        "ports": {
            "game": 30000,
            "rcon": 30100,
        },
        "public": {},
        "extra": {
            "memory": "2G",
        },
        "image": podman_jdk_image,
        "run_command": paper_command,
        "mounts": [*common_mounts],
    },
    "build": {
        "ports": {
            "game": 30001,
            "rcon": 30101,
            "dynmap": 30201,
            "schemati": 8080,
        },
        "public": {"dynmap"},
        "extra": {
            "memory": "8G",
        },
        "image": podman_jdk_image,
        "run_command": paper_command,
        "mounts": [*common_mounts, dynmap_mount],
    },
    "school": {
        "ports": {
            "game": 30002,
            "rcon": 30102,
        },
        "public": {},
        "extra": {
            "memory": "4G",
        },
        "image": podman_jdk_image,
        "run_command": paper_command,
        "mounts": [*common_mounts],
    },
    "survival": {
        "ports": {
            "game": 30003,
            "rcon": 30103,
        },
        "public": {},
        "extra": {
            "memory": "4G",
        },
        "image": podman_jdk_image,
        "run_command": paper_command,
        "mounts": [*common_mounts],
    },
    "play": {
        "ports": {
            "game": 30004,
            "rcon": 30104,
        },
        "public": {},
        "extra": {
            "memory": "4G",
        },
        "image": podman_jdk_image,
        "run_command": paper_command,
        "mounts": [*common_mounts],
    },
    "boat": {
        "ports": {
            "game": 30005,
            "rcon": 30105,
        },
        "public": {},
        "extra": {
            "memory": "4G",
        },
        "image": podman_jdk_image,
        "run_command": paper_command,
        "mounts": [*common_mounts],
    },
    "competition": {
        "ports": {
            "game": 30006,
            "rcon": 30106,
        },
        "public": {},
        "extra": {
            "memory": "4G",
        },
        "image": podman_jdk_image,
        "run_command": paper_command,
        "mounts": [*common_mounts],
    },
    "prodxy": {
        "ports": {
            "game": 25565,
        },
        "public": {"game"},
        "extra": {
            "memory": "1G",
        },
        "image": podman_jdk_image,
        "run_command": waterfall_command,
        "mounts": [*common_mounts],
    }
}


SERVERS_LOCATION = Path("/home/mcadmin/prod")
DESTINATION = Path("/store/backups")
