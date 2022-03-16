import tarfile


def make_tar(source, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    destination = output.with_suffix(".tar.gz")
    with tarfile.open(destination, "w:gz") as tar:
        tar.add(source, arcname=source.name)
