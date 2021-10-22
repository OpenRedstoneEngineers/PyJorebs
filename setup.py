from setuptools import setup, find_packages

setup(
    name="PyJorebs",
    version="0.0.1",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "pyjorebs-test=pyjorebs.testing:do_test"
        ]
    }
)
