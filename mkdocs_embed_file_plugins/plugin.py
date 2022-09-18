import codecs
from typing import Union, List, Tuple, Dict, Any
import os
import re
from glob import iglob
from pathlib import Path
from urllib.parse import unquote, quote
import ast
import frontmatter
import markdown
from bs4 import BeautifulSoup
from mdx_wikilink_plus.mdx_wikilink_plus import WikiLinkPlusExtension
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from mkdocs_callouts.plugin import CalloutsPlugin
from custom_attributes.plugin import convert_text_attributes


def search_in_file(citation_part: str, contents: str) -> str:
    """
    Search a part in the file
    Args:
        citation_part: The part to find
        contents: The file contents
    Returns: the part found
    """
    data = contents.split('\n')
    if '#' not in citation_part:
        # All text citation
        return contents
    elif '#' in citation_part and not '^' in citation_part:
        # cite from title
        sub_section = []
        citation_part = citation_part.replace('-', ' ').replace('#', '# ').upper()
        heading = 0
        for i in data:
            if citation_part in i.upper() and i.startswith('#'):
                heading = i.count('#') * (-1)
                sub_section.append([i])
            elif heading != 0:
                inverse = i.count('#') * (-1)
                if inverse == 0 or heading > inverse:
                    sub_section.append([i])
                elif inverse >= heading:
                    break
        sub_section = [x for y in sub_section for x in y]

        sub_section = '\n'.join(sub_section)
        return sub_section
    elif '#^' in citation_part:
        # cite from block
        citation_part = citation_part.replace('#', '')
        for i in data:
            if citation_part in i.upper():
                return i.replace(citation_part, '')
    return ''


def mini_ez_links(urlo, base, end, url_whitespace, url_case):
    base, url_blog, md_link_path = base
    url_blog_path = [x for x in url_blog.split('/') if len(x) > 0]
    url_blog_path = url_blog_path[len(url_blog_path) - 1]
    internal_link = Path(md_link_path, urlo[2]).resolve()
    if os.path.isfile(internal_link):
        internal_link = str(internal_link).replace(base, '')
    else:  # fallback to searching
        if urlo[2].endswith('.md'):
            internal_link = str(search_file_in_documentation(Path(urlo[2]).resolve(), Path(md_link_path).parent))
        if not os.path.isfile(internal_link): # manual search
            file_name = urlo[2].replace('index', '')
            file_name = file_name.replace('../', '')
            file_name = file_name.replace('./', '')

            all_docs = [
                re.sub(rf"(.*)({url_blog_path})?/docs/*", '', x.replace('\\', '/')).replace(
                    '.md', ''
                )
                for x in iglob(str(base) + os.sep + '**', recursive=True)
                if os.path.isfile(x)
            ]
            file_found = [
                '/' + x for x in all_docs if os.path.basename(x) == file_name or x == file_name
            ]
            if file_found:
                internal_link = file_found[0]
            else:
                return file_name
    file_path = internal_link.replace(base, '')
    url = file_path.replace('\\', '/').replace('.md', '')
    url = url.replace('//', '/')
    url = url_blog[:-1] + quote(url)
    if not url.startswith(('https:/', 'http:/')):
        url = 'https://' + url
    if not url.endswith('/') and not url.endswith(('png', 'jpg', 'jpeg', 'gif', 'webm')):
        url = url + '/'
    return url


def strip_comments(markdown):
    file_content = markdown.split('\n')
    markdown = ''
    for line in file_content:
        if not re.search(r'%%(.*)%%', line) or not line.startswith('%%') or not line.endswith('%%'):
            markdown += line + '\n'
    markdown = re.sub(r'%%(.*)%%', '', markdown, flags=re.DOTALL)
    return markdown

def cite(md_link_path, link, soup, citation_part, config, callouts, custom_attr) -> BeautifulSoup:
    """Append the content of the founded file to the original file.

    Args:
        md_link_path: File found
        link: Line with the citation
        soup: HTML of the original files
        citation_part: Part to find
        config: the config file
    Returns: updated HTML
    """
    docs = config['docs_dir']
    url = config['site_url']

    md_config = {
        'mdx_wikilink_plus': {
            'base_url': (docs, url, md_link_path),
            'build_url': mini_ez_links,
            'image_class': 'wikilink',
        }
    }
    new_uri = str(md_link_path).replace(str(docs), str(url))
    new_uri = new_uri.replace('\\', '/')
    new_uri = new_uri.replace('.md', '/')
    new_uri = new_uri.replace('//', '/')
    new_uri = re.sub('https?:\/', '\g<0>/', new_uri)
    input_file = codecs.open(str(md_link_path), mode='r', encoding='utf-8')
    text = input_file.read()

    contents = frontmatter.loads(text).content
    quote = search_in_file(citation_part, contents)
    tooltip_template = (
            "<div class='not_found'>" +
            str(link['src'].replace('/', '')) + '</div>'
    )
    if len(quote) > 0:
        if callouts:
            quote = CalloutsPlugin().on_page_markdown(quote, None, None, None)
        if len(custom_attr) > 0:
            config_attr = {
                'file': custom_attr,
                'docs_dir': docs
            }
            quote = convert_text_attributes(quote, config_attr)
        quote = strip_comments(quote)
        html = markdown.markdown(
            quote,
            extensions=[
                'nl2br',
                'footnotes',
                'attr_list',
                'mdx_breakless_lists',
                'smarty',
                'sane_lists',
                'tables',
                'admonition',
                WikiLinkPlusExtension(md_config['mdx_wikilink_plus']),
            ],
        )
        link_soup = BeautifulSoup(html, 'html.parser')
        if link_soup:
            tooltip_template = (
                "<div class='citation'> <a href='"
                + str(new_uri)
                + "' class='link_citation'><i class='fas fa-link'></i> </a>"
                + str(link_soup).replace(
                    '!<img class="wikilink', '<img class="wikilink'
                )
                + '</div>'
            )
    else:
        tooltip_template = (
            "<div class='not_found'>" +
            str(link['src'].replace('/', '')) + '</div>'
        )
    new_soup = str(soup).replace(str(link), str(tooltip_template))
    soup = BeautifulSoup(new_soup, 'html.parser')
    return soup


def create_link(link):
    if link.endswith('/'):
        return link[:-1] + '.md'
    else:
        return link + '.md'

def search_file_in_documentation(link: Union[Path,str], config_dir: Path) -> Union[Path, int]:
    file_name = os.path.basename(link)
    if not file_name.endswith('.md'):
        file_name = file_name + '.md'
    for p in config_dir.rglob(f"*{file_name}"):
        return p
    return 0


class EmbedFile(BasePlugin):
    config_scheme = (
        ('callouts', config_options.Type(bool, default=False)),
        ('custom-attributes', config_options.Type(str, default=''))
    )

    def __init__(self):
        self.enabled = True
        self.total_time = 0

    def on_post_page(self, output_content, page, config) -> str:
        soup = BeautifulSoup(output_content, 'html.parser')
        docs = Path(config['docs_dir'])
        md_link_path = ''
        callout = self.config['callouts']
        for link in soup.findAll(
                'img',
                src=lambda src: src is not None 
                    and 'favicon' not in src 
                    and not src.endswith(('png', 'jpg', 'jpeg', 'gif', 'svg')) 
                    and not 'www' in src 
                    and not 'http' in src 
                    and not '://' in src,
        ):
            if len(link['src']) > 0:


                if link['src'][0] == '.':  # relative links
                    md_src = create_link(unquote(link['src']))
                    md_link_path = Path(
                        os.path.dirname(page.file.abs_src_path), md_src).resolve()
                    if not os.path.isfile(md_link_path):
                        md_link_path = search_file_in_documentation(md_link_path, docs)

                elif link['src'][0] == '/':
                    md_src_path = create_link(unquote(link['src']))
                    md_link_path = os.path.join(
                        config['docs_dir'], md_src_path)
                    md_link_path = Path(unquote(md_link_path)).resolve()

                elif link['src'][0] != '#':
                    md_src_path = create_link(unquote(link['src']))

                    md_link_path = os.path.join(
                        os.path.dirname(page.file.abs_src_path), md_src_path
                    )
                    md_link_path = Path(unquote(md_link_path)).resolve()
            else:
                md_src_path = create_link(unquote(link['src']))
                md_link_path = os.path.join(
                    os.path.dirname(page.file.abs_src_path), md_src_path
                )
                md_link_path = Path(unquote(md_link_path)).resolve()

            if md_link_path != '' and len(link['src']) > 0:
                if '#' in link.get('alt', ''):
                    # heading
                    citation_part = re.sub('^(.*)#', '#', link['alt'])
                elif '#' in link.get('src', ''):
                    citation_part = re.sub('^(.*)#', '#', link['src'])
                else:
                    citation_part = link.get('alt', False)
                if citation_part:
                    md_link_path = re.sub(
                        '#(.*)\.md', '.md', str(md_link_path))
                    md_link_path = md_link_path.replace('\.md', '.md')
                    md_link_path = Path(md_link_path)
                    if os.path.isfile(md_link_path):
                        soup = cite(md_link_path, link, soup,
                                    citation_part, config, callout, self.config['custom-attributes'])
                    else:
                        link_found=search_file_in_documentation(md_link_path, docs)
                        if link_found != 0:
                            soup = cite(link_found, link, soup,
                                        citation_part, config, callout, self.config['custom-attributes'])
        return str(soup)
