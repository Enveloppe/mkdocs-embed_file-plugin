import shutil
from pathlib import Path
from typing import Any

from setuptools import find_packages, setup

version = "2.0.9"

requirements = Path("requirements.txt")
readme = Path("README.md")


def classification_dependencies() -> tuple[list[Any], list[Any]]:
    with requirements.open("r", encoding="UTF-8") as f:
        external = []
        internal = []
        for package in f.read().splitlines():
            if package.startswith("git+"):
                external.append(package.replace("git+", ""))
            else:
                internal.append(package)
    return external, internal


with readme.open("r", encoding="utf-8") as fh:
    long_description = fh.read()

external, internal = classification_dependencies()

# remove old dist version

shutil.rmtree("dist", ignore_errors=True)

setup(
    name="mkdocs_embed_file_plugins",
    python_requires=">=3.7",
    version=version,
    description="A plugin to quote file from docs",
    author="Mara-Li",
    author_email="mara-li@icloud.com",
    packages=find_packages(),
    install_requires=internal,
    dependency_links=external,
    license="AGPL",
    keywords="obsidian, obsidian.md, mkdocs, file, embed, cite, quote",
    classifiers=[
        "Natural Language :: English",
        "Natural Language :: French",
        "Topic :: Text Processing :: Markup :: Markdown",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later"
        " (AGPLv3+)",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ObsidianPublisher/mkdocs-embed_file-plugin",
    entry_points={
        "mkdocs.plugins": ["embed_file=mkdocs_embed_file_plugins.plugin:EmbedFile"]
    },
)
