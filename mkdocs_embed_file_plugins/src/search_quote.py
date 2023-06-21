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
                print("found!", i.replace(citation_part, ""))
                return i.replace(citation_part, "")
    return ""


def search_file_in_documentation(
    link: Union[Path, str], config_dir: Path, base: any
) -> Union[Path, int]:
    file_name = os.path.basename(link)
    if not file_name.endswith(".md"):
        file_name = file_name + ".md"
    if not file_name.startswith("index"):
        for p in config_dir.rglob(f"*{file_name}"):
            return p
    else:
        baseParent = Path(base).parents
        linksParent = Path(link).parents
        # find the common parent
        linksBaseEquals = [i for i in linksParent if i in baseParent][0]
        relative = Path(str(link).replace(str(linksBaseEquals), ""))
        for p in Path(base).rglob(f"**{relative}"):
            return p
    return 0
