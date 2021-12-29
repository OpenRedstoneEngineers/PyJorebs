#!/usr/bin/env python3
import sys
import subprocess

from config import SERVICES


def mounts_to_args(mounts, replacements):
    for a, b in mounts:
        yield "-v"
        yield f"{a.format(**replacements)}:{b.format(**replacements)}"


def ports_to_args(ports, public):
    for name, port in ports.items():
        if not isinstance(port, tuple):
            port = port, port
        host_port, container_port = port
        ip = "0.0.0.0" if name in public else "127.0.0.1"
        yield "-p"
        yield f"{ip}:{host_port}:{container_port}"


# TODO: create a propORE argument parsORE (or something)
def main(service, unit_name, runtime_dir, extra_args="", dry_run=False):
    service_config = SERVICES[service]
    # so tihs is weird XD
    # TODO: server -> service
    replacements = {**service_config["extra"], "server": service, "extra_args": extra_args}
    mounts = mounts_to_args(service_config["mounts"], replacements)
    publications = ports_to_args(service_config["ports"], service_config["public"])
    def get(x):
        if x not in service_config:
            return None
        return service_config[x].format(**replacements)

    run_command = get("run_command")
    command_parts = [] if run_command is None else ["sh", "-c", run_command]

    podman_command = [
        "/usr/bin/podman", "run",
        "--conmon-pidfile", f"{runtime_dir}/{unit_name}-pid",
        "--cgroups", "no-conmon",
        "--name", service,
        "--net", "slirp4netns:allow_host_loopback=true,port_handler=slirp4netns",
        *mounts,
        *publications,
        "--rm", "-dit",
        service_config["image"],
        *command_parts,
    ]
    if dry_run:
        print(" ".join(podman_command))
    else:
        subprocess.run(podman_command, stdout=sys.stdout, stderr=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:])
