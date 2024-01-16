import os
import shutil
from pathlib import Path

from setuptools import find_packages, setup

version = "0.1.0"
name = "pytunegrab"

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
    
with open("requirements.txt", "r", encoding="utf-8") as req_files:
    install_requires = req_files.read().splitlines()

setup(
    name=name,
    version=version,
    packages=find_packages(),
    install_requires=install_requires,
    long_description=long_description,
    long_description_content_type="text/markdown",
)


def move_dist(version: str) -> None:
    """Move files in dist to the correct version folder.

    Args:
        version (str): The version number.
    """
    dist_path = Path("dist")
    version_path = dist_path / version

    # Cria o diretório da versão se ainda não existir
    version_path.mkdir(parents=True, exist_ok=True)

    for file_name in os.listdir(dist_path):
        file_path = dist_path / file_name

        # Verifica se é um arquivo (não é um diretório)
        if file_path.is_file():
            # Move o arquivo para o diretório da versão
            shutil.move(file_path, version_path / file_name)


move_dist(version)
