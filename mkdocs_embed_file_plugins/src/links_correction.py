from glob import iglob
from pathlib import Path
import os
import re
from urllib.parse import quote

from mkdocs_embed_file_plugins.src.search_quote import search_file_in_documentation

import re
from pathlib import Path
MULTIMEDIA_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",  # Images
    ".mp4", ".avi", ".mov", ".mkv",  # Vidéos
    ".mp3", ".wav", ".flac",  # Audio
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",  # Documents
)

def mini_ez_links(link, base, end, url_whitespace, url_case):
    base_data, url_blog, md_link_path = base
    url_blog_path = [x for x in url_blog.split("/") if x]
    url_blog_path = url_blog_path[-1]

    # Vérifie si c'est une image (ne pas ajouter notfound:: pour les images)
    if any(link[2].lower().endswith(ext) for ext in MULTIMEDIA_EXTENSIONS) :
        internal_link = Path(md_link_path, link[2]).resolve()
        if internal_link.is_file() :
            return create_url(internal_link, link[2], base, url_blog_path, True)
        else :
            # Retourne simplement le chemin brut pour les fichiers multimédias non trouvés
            return link[2]

    # Résout le chemin interne pour les fichiers Markdown
    internal_link = Path(md_link_path, link[2]).resolve()
    if internal_link.is_file():
        return create_url(internal_link, link[2], base, url_blog_path, True)

    # Si le fichier Markdown n'est pas trouvé, marque avec "notfound::"
    return f"notfound::{create_url(internal_link, link[2], base, url_blog_path, True)}"

def convert_links_if_markdown(quote_str, base):
    """Convert links if the file is a markdown file."""
    # Search for links
    links = re.findall(r"\[([^\]]*)\]\(([^\)]*)\)", quote_str)
    base_data, url_blog, md_link_path = base
    if not url_blog:
        raise Exception("site_url is not defined in mkdocs.yml")

    url_blog_path = [x for x in url_blog.split("/") if x]
    url_blog_path = url_blog_path[-1]
    for link in links:
        if not link[1].startswith("http"):
            internal_link = Path(md_link_path, link[1]).resolve()
            url = create_url(internal_link, link[1], base, url_blog_path, False)
            quote_str = quote_str.replace(link[1], url)
    return quote_str


def create_url(internal_link, link, base, url_blog_path, wikilinks=False) :
    base, url_blog, md_link_path = base
    internal_path = Path(internal_link)
    # Vérifie si le lien est une image ou un fichier multimédia
    if any(link.lower().endswith(ext) for ext in MULTIMEDIA_EXTENSIONS) :
        # Normalise le chemin des images sans les transformer en URLs Markdown
        image_path = Path(url_blog) / link.replace("\\", "/")
        final_url = str(image_path).replace("\\", "/")
        return final_url

    # Vérifie si le chemin est un fichier Markdown valide
    if internal_path.is_file() :
        internal_link = str(internal_path).replace(str(base), "")
    else :
        resolved = search_file_in_documentation(link, md_link_path.parent, base)

        # Fallback explicite pour `/index.md` via dossier parent
        if resolved == 0 and not link.endswith("index.md") :
            folder_name = os.path.splitext(link)[0]
            resolved = search_file_in_documentation(f"{folder_name}/index.md", md_link_path.parent, base)

        if resolved == 0 :
            internal_link = str(link).replace("../", "").replace("./", "").replace(".md", "")
        else :
            internal_link = str(resolved).replace(str(base), "")

    # Normalisation du chemin final pour les fichiers Markdown
    filepath = internal_link.replace("\\", "/").replace(".md", "")
    url = re.sub(r"/+$", "", str(url_blog)) + "/" + quote(filepath)

    # Ajout du protocole si manquant
    if not url.startswith("http") :
        url = "https://" + url
    if not url.endswith("/") and not re.search(r"\\.(.*)$", url) :
        url += "/"

    return url
