import codecs
import os
import re
from pathlib import Path
from urllib.parse import unquote
import frontmatter
import markdown
from bs4 import BeautifulSoup
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from mkdocs_callouts.plugin import CalloutsPlugin
from custom_attributes.plugin import convert_text_attributes
import logging

from mkdocs_embed_file_plugins.src.links_correction import (
    MULTIMEDIA_EXTENSIONS, convert_links_if_markdown,
    mini_ez_links,
    )
from mkdocs_embed_file_plugins.src.search_quote import (
    search_file_in_documentation,
    search_in_file,
)
from mkdocs_embed_file_plugins.src.utils import add_not_found_class, create_link, strip_comments


def cite(
    md_link_path, link, soup, citation_part, config, callouts, custom_attr, msg
) -> BeautifulSoup:
    """Append the content of the founded file to the original file.

    Args:
        md_link_path (str): Path of the file to be modified.
        link (str): Link to the file to be included.
        soup (BeautifulSoup): BeautifulSoup object of the file to be modified.
        citation_part (str): Part of the link to be included.
        config (dict): Configuration of the plugin.
        callouts (CalloutsPlugin): Callouts plugin.
        custom_attr (CustomAttributesPlugin): Custom attributes plugin.
        msg (str): Message to be displayed if the file is not found.
    Returns: updated HTML
    """
    docs = config["docs_dir"]
    url = config["site_url"]

    md_config = {
        "mdx_wikilink_plus": {
            "base_url": (docs, url, md_link_path),
            "build_url": mini_ez_links,
            "image_class": "wikilink",
        }
    }
    new_uri = str(md_link_path).replace(str(docs), str(url))
    new_uri = new_uri.replace("\\", "/")
    new_uri = new_uri.replace(".md", "/")
    new_uri = new_uri.replace("//", "/")
    new_uri = re.sub("https?:\\/", "\\g<0>/", new_uri)
    new_uri = new_uri.replace("/index/", "/")
    input_file = codecs.open(str(md_link_path), mode="r", encoding="utf-8")
    text = input_file.read()

    contents = frontmatter.loads(text).content
    quote = search_in_file(citation_part, contents)
    tooltip_template = (
        "<div class='citation'> <a href='"
        + str(link["src"])
        + "' class='link_citation'><i class='fas fa-link'></i> </a>"
        + str(link["alt"])
        + " not exists."
        + "</div>"
    )
    if len(quote) > 0:
        if callouts:
            quote = CalloutsPlugin().on_page_markdown(quote, None, None, None)
        if len(custom_attr) > 0:
            config_attr = {"file": custom_attr, "docs_dir": docs}
            quote = convert_text_attributes(quote, config_attr)
        quote = convert_links_if_markdown(quote, (docs, url, md_link_path))
        quote = strip_comments(quote)
        md_extensions = config["markdown_extensions"]
        md_extensions.append("mdx_wikilink_plus")
        html = markdown.markdown(
            quote, extensions=md_extensions, extension_configs=md_config
        )
        link_soup = BeautifulSoup(html, "html.parser")
        if link_soup:
            tooltip_template = (
                "<div class='citation'> <a href='"
                + str(new_uri)
                + "' class='link_citation'><i class='fas fa-link'></i> </a>"
                + str(link_soup).replace(
                    '!<img class="wikilink', '<img class="wikilink'
                )
                + "</div>"
            )
            new_soup = str(soup).replace(str(link), str(tooltip_template))
            soup = BeautifulSoup(new_soup, "html.parser")
            return soup
    else:
        log = logging.getLogger("mkdocs.plugins." + __name__)
        log.info(
            "[EMBED FILE PLUGIN] CITATION NOT FOUND : "
            + unquote(citation_part)
            + "for : "
            + str(md_link_path)
            + " with link: "
            + str(link)
            + " and new_uri: "
            + str(new_uri)
            + " and quote: "
            + str(quote)
        )
        return tooltip_not_found(link, soup, msg)


def tooltip_not_found(link, soup, msg) -> BeautifulSoup:
    tooltip_template = (
        "<div class='citation'> <a class='link_citation'><i class='fas fa-link'></i> </a>"
        + f'<p style="text-align: center; display: block"><i class="not_found" src={link["src"]}>'
        + str(link["alt"])
        + f"</i> {msg}</p>"
        + "</div>"
    )
    new_soup = str(soup).replace(str(link), str(tooltip_template))
    soup = BeautifulSoup(new_soup, "html.parser")
    return soup


class EmbedFile(BasePlugin):
    config_scheme = (
        ("callouts", config_options.Type(bool, default=False)),
        ("custom-attributes", config_options.Type(str, default="")),
        ("language_message", config_options.Type(str, default="file not exists")),
    )

    def __init__(self):
        self.enabled = True
        self.total_time = 0

    def on_post_page(self, output_content, page, config) -> str:
        soup = BeautifulSoup(output_content, "html.parser")
        docs = Path(config["docs_dir"])
        md_link_path = ""
        callout = self.config["callouts"]
        language_message = self.config["language_message"]
        for link in soup.findAll(
            "img",
            src=lambda src: src is not None
            and "favicon" not in src
            and not any(src.lower().endswith(ext) for ext in MULTIMEDIA_EXTENSIONS)
            and "www" not in src
            and "http" not in src
            and "://" not in src,
        ):
            if len(link["src"]) > 0:
                if link["src"].startswith("./"):
                    md_link_path = page.file.abs_src_path
                elif link["src"][0] == ".":  # relative links
                    md_src = create_link(unquote(link["src"]))
                    md_link_path = Path(
                        os.path.dirname(page.file.abs_src_path), md_src
                    ).resolve()
                    md_link_path = re.sub(r"[\/\\]?#(.*)$", "", str(md_link_path))
                    if not os.path.isfile(md_link_path):
                        md_link_path = search_file_in_documentation(
                            md_link_path, docs, docs
                        )

                elif link["src"][0] == "/":
                    md_src_path = create_link(unquote(link["src"]))
                    md_link_path = os.path.join(config["docs_dir"], md_src_path)
                    md_link_path = Path(unquote(md_link_path)).resolve()

                elif link["src"][0] != "#":
                    md_src_path = create_link(unquote(link["src"]))
                    md_link_path = os.path.join(
                        os.path.dirname(page.file.abs_src_path), md_src_path
                    )
                    md_link_path = re.sub(r"/#(.*).md$", ".md", str(md_link_path))
                    md_link_path = Path(unquote(md_link_path)).resolve()

            else:
                md_src_path = create_link(unquote(link["src"]))
                md_link_path = os.path.join(
                    os.path.dirname(page.file.abs_src_path), md_src_path
                )
                md_link_path = Path(unquote(md_link_path)).resolve()
            if md_link_path == 0:
                soup = tooltip_not_found(link, soup, language_message)
            if (md_link_path != "" or md_link_path == 0) and len(link["src"]) > 0:
                if "#" in link.get("alt", ""):
                    # heading
                    citation_part = re.sub("^(.*)#", "#", link["alt"])
                elif "#" in link.get("src", ""):
                    citation_part = re.sub("^(.*)#", "#", unquote(link["src"]))
                else:
                    citation_part = link.get("alt", False)
                if citation_part:
                    md_link_path = Path(str(md_link_path))

                    if os.path.isfile(md_link_path):
                        soup = cite(
                            md_link_path,
                            link,
                            soup,
                            citation_part,
                            config,
                            callout,
                            self.config["custom-attributes"],
                            language_message,
                        )
                    else:
                        link_found = search_file_in_documentation(
                            md_link_path, docs, docs
                        )
                        if link_found != 0:
                            soup = cite(
                                link_found,
                                link,
                                soup,
                                citation_part,
                                config,
                                callout,
                                self.config["custom-attributes"],
                                language_message,
                            )
        return add_not_found_class(str(soup))
