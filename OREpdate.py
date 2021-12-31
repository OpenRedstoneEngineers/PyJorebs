import requests
import yaml
from pathlib import Path
from collections import namedtuple

Download = namedtuple("Download", "url path")

def do_download(download: Download, into: Path):
    r = requests.get(download.url)
    r.raise_for_status()
    (into / download.path).write_bytes(r.content)


def download_from_papermc(project: str, version: str) -> Download:
    r = requests.get(f"https://papermc.io/api/v2/projects/{project}/versions/{version}")
    r.raise_for_status()
    latest_build = r.json()["builds"][-1]
    r = requests.get(f"https://papermc.io/api/v2/projects/{project}/versions/{version}/builds/{latest_build}")
    r.raise_for_status()
    # name -> sha256 would give a hash
    download = r.json()["downloads"]["application"]["name"]
    return Download(
        url=f"https://papermc.io/api/v2/projects/{project}/versions/{version}/builds/{latest_build}/downloads/{download}",
        path=download,
    )


github_base_url = "https://api.github.com"


def get_releases(repository):
    r = requests.get(f"{github_base_url}/repos/{repository}/releases")
    r.raise_for_status()
    return r.json()


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
