import requests
import yaml
from pathlib import Path
from collections import namedtuple

Download = namedtuple("Download", "url path")

def do_download(download: Download, into: Path):
    r = requests.get(download.url)
    r.raise_for_status()
    (into / download.path).write_bytes(r.content)


PAPER_API = "https://papermc.io/api/v2"
GITHUB_API = "https://api.github.com"
# job: LuckPerms
LUCKO_JENKINS = "https://ci.lucko.me"
# job: LibertyBans
LIBERTY_JENKINS = "https://ci.hahota.net"


def rest_get(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.json()


def jenkins_build(base_url, job):
    # also has number which is build number
    return rest_get(f"{base_url}/job/{job}/lastSuccessfulBuild/api/json")


def jenkins_artifact(base_url, job, artifact_type):
    build_info = jenkins_build(base_url, job)
    artifact = next(artifact for artifact in build_info["artifacts"] if artifact["fileName"].find(artifact_type) != -1)
    url = artifact["relativePath"]
    return Download(
        url=f"{base_url}/job/{job}/lastSuccessfulBuild/artifact/{url}",
        path=artifact["fileName"],
    )


def papermc_project(project):
    return rest_get(f"{PAPER_API}/projects/{project}")
def papermc_version(project, version):
    return rest_get(f"{PAPER_API}/projects/{project}/versions/{version}")
def papermc_build(project, version, build):
    return rest_get(f"{PAPER_API}/projects/{project}/versions/{version}/builds/{build}")


def papermc_download_latest(project: str, version: str) -> Download:
    version_info = papermc_version(project=project, version=version)
    latest_build = version_info["builds"][-1]
    # name -> sha256 would give a hash
    build_info = papermc_build(project=project, version=version, build=latest_build)
    download = build_info["downloads"]["application"]["name"]
    return Download(
        url=f"{PAPER_API}/projects/{project}/versions/{version}/builds/{latest_build}/downloads/{download}",
        path=download,
    )


def github_releases(repository):
    return rest_get(f"{GITHUB_API}/repos/{repository}/releases")


def extract_plugin_info_from_jar(jar_file: Path):
    from zipfile import ZipFile
    with ZipFile(jar_file, "r") as jar, jar.open("plugin.yml", "r") as plugin:
        return yaml.safe_load(plugin)


plugin_sources = {
    "NBTAPI": ["github", "tr7zw/Item-NBT-API"],
}


def print_plugin_versions(plugin_dir):
    for x in plugin_dir.glob("*.jar"):
        info = extract_plugin_info_from_jar(x)
        name, version = info["name"], info["version"]
        print(f"{name}: {version}")
