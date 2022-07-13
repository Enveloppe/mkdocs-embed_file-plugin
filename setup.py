from setuptools import setup, find_packages

version = "1.2.12"

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
with open("requirements.txt") as f:
    required = f.read().splitlines()
setup(
    name="mkdocs_embed_file_plugins",
    python_requires=">=3.7",
    version=version,
    description="A plugin to quote file from docs",
    author="Mara-Li",
    author_email="mara-li@icloud.com",
    packages=find_packages(),
    install_requires=required,
    license="AGPL",
    keywords="obsidian, obsidian.md, mkdocs, file, embed, cite, quote",
    classifiers=[
        "Natural Language :: English",
        "Natural Language :: French",
        "Topic :: Text Processing :: Markup :: Markdown",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later"
        " (AGPLv3+)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Mara-Li/mkdocs_embed_file_plugins",
    entry_points={
        "mkdocs.plugins": ["embed_file =mkdocs_embed_file_plugins.plugin:EmbedFile"]
    },
)
