#!/usr/bin/env python3
import sys
import subprocess

image_name = "docker.io/library/openjdk:16.0.1-slim"

def mounts_to_args(*mounts):
    for (a, b) in mounts:
        yield "-v"
        yield f"{a}:{b}"

def main(server, unit_name, runtime_dir):
    mounts = mounts_to_args(
        [f"/home/mcadmin/prod/{server}", "/data"],
        ["/home/mcadmin/prod/paper", "/common"],
        [f"/store/tiles/{server}", "/data/plugins/dynmap/web/tiles"],
    )
    # java opts?
    paper_start_command = ["sh", "-c", "cd /data && exec java -jar /common/paper.jar"]
    podman_command = [
        "/usr/bin/podman", "run",
        "--conmon-pidfile", f"{runtime_dir}/{unit_name}-pid",
        "--cidfile", f"{runtime_dir}/{unit_name}-cid",
        "--cgroups", "no-conmon",
        "--name", f"mcserver-{server}",
        *mounts,
        # pod?
        "--rm", "-dit",
        image_name,
        *paper_start_command,
    ]
    subprocess.run(podman_command, stdout=sys.stdout, stderr=sys.stderr)
    
if __name__ == "__main__":
    main(*sys.argv[1:])
