import os
import re
from pathlib import Path
from typing import Union


def search_in_file(citation_part: str, contents: str) -> str:
    """
    Search a part in the file
    Args:
        citation_part: The part to find
        contents: The file contents
    Returns: the part found
    """
    data = contents.split("\n")
    if "#" not in citation_part:
        # All text citation
        return re.sub(r"\[?\^\w+$", "", contents)
    elif "#" in citation_part and "^" not in citation_part:
        # cite from title
        sub_section = []
        citation_part = citation_part.replace("-", " ").replace("#", "# ").upper()
        heading = 0

        for i in data:
            if citation_part in i.upper() and i.startswith("#"):
                heading = i.count("#") * (-1)
                sub_section.append([i])
            elif heading != 0:
                inverse = i.count("#") * (-1)
                if inverse == 0 or heading > inverse:
                    sub_section.append([i])
                elif inverse >= heading:
                    break
        sub_section = [x for y in sub_section for x in y]
        sub_section = [re.sub(r"\[?\^\w+$", "", x) for x in sub_section]
        sub_section = "\n".join(sub_section)
        return sub_section
    elif "#^" in citation_part:
        # cite from block
        citation_part = citation_part.replace("#", "")
        for i in data:
            if re.search(re.escape(citation_part) + "$", i):
                return i.replace(citation_part, "")
    return ""


def search_file_in_documentation(link: Union[Path, str], config_dir: Path, base: Path) -> Union[Path, int]:
    """
    Recherche un fichier spécifique dans la documentation.
    """
    file_name = os.path.basename(link)

    # Ignorer les liens non pertinents (par exemple, images, scripts, etc.)
    if not re.search(r"(\.md$|[^./\\]+$)", file_name, re.IGNORECASE):
        return 0

    # Ajout de ".md" si absent
    if not file_name.endswith(".md"):
        file_name += ".md"

    # Recherche directe du fichier dans la structure
    for p in config_dir.rglob(f"*{file_name}"):
        return p

    # Recherche un dossier correspondant au nom sans extension
    folder_name = os.path.splitext(file_name)[0]
    folder_path = config_dir / folder_name / "index.md"
    if folder_path.is_file():
        return folder_path

    # Recherche élargie dans tous les sous-dossiers
    for parent in config_dir.rglob("*"):
        potential_path = parent / folder_name / "index.md"
        if potential_path.is_file():
            return potential_path

    # Aucun fichier trouvé

    return 0
