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


def rest_get(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.json()


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
