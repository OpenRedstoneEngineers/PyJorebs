#!/usr/bin/env python3
import sys
import subprocess

from config import SERVERS, PODMAN_IMAGE_NAME


def mounts_to_args(mounts, replacements):
    for a, b in mounts:
        yield "-v"
        yield f"{a.format(**replacements)}:{b.format(**replacements)}"


def ports_to_args(ports, public):
    for name, port in ports.items():
        ip = "0.0.0.0" if name in public else "127.0.0.1"
        yield "-p"
        yield f"{ip}:{port}:{port}"


def main(server, unit_name, runtime_dir, dry_run=False):
    server_config = SERVERS[server]
    # so tihs is weird XD
    replacements = {**server_config["extra"], "server": server}
    mounts = mounts_to_args(server_config["mounts"], replacements)
    publications = ports_to_args(server_config["ports"], server_config["public"])
    def get(x):
        return server_config[x].format(**replacements)

    run_command = get("run_command")

    podman_command = [
        "/usr/bin/podman", "run",
        "--conmon-pidfile", f"{runtime_dir}/{unit_name}-pid",
        "--cidfile", f"{runtime_dir}/{unit_name}-cid",
        "--cgroups", "no-conmon",
        "--name", f"mc-{server}",
        "--pod", "prod-network",
        *mounts,
        *publications,
        "--rm", "-dit",
        PODMAN_IMAGE_NAME,
        "sh", "-c",
        run_command,
    ]
    if dry_run:
        print(" ".join(podman_command))
    else:
        subprocess.run(podman_command, stdout=sys.stdout, stderr=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:])
