from glob import iglob
from pathlib import Path
import os
import re
from urllib.parse import quote

from mkdocs_embed_file_plugins.src.search_quote import search_file_in_documentation


def mini_ez_links(link, base, end, url_whitespace, url_case) :
    base_data, url_blog, md_link_path = base
    url_blog_path = [x for x in url_blog.split('/') if len(x) > 0]
    url_blog_path = url_blog_path[len(url_blog_path) - 1]
    internal_link = Path(md_link_path, link[2]).resolve()
    return create_url(internal_link, link[2], base, url_blog_path, True)


def convert_links_if_markdown(quote_str, base) :
    """Convert links if the file is a markdown file."""
    # search for links
    links = re.findall(r'\[([^\]]*)\]\(([^\)]*)\)', quote_str)
    base_data, url_blog, md_link_path = base
    url_blog_path = [x for x in url_blog.split('/') if len(x) > 0]
    url_blog_path = url_blog_path[len(url_blog_path) - 1]
    for link in links :
        if not link[1].startswith('http') :
            internal_link = Path(md_link_path, link[1]).resolve()
            url = create_url(internal_link, link[1], base, url_blog_path, False)
            quote_str = quote_str.replace(link[1], url)
    return quote_str


def create_url(internal_link, link, base, url_blog_path, wikilinks=False) :
    base, url_blog, md_link_path = base
    if os.path.isfile(internal_link) :
        internal_link = str(internal_link).replace(base, '')
    else :
        if link.endswith('.md') :
            if wikilinks :
                internal_link = str(search_file_in_documentation(Path(link).resolve(), md_link_path.parent))
            else :
                internal_link = str(search_file_in_documentation(link, md_link_path.parent))
        if not os.path.isfile(internal_link) :
            file_name = link.replace('index', '')
            file_name = file_name.replace('../', '')
            file_name = file_name.replace('./', '')
            file_name = file_name.replace('.md', '')
            all_docs = [
                re.sub(rf"(.*)({url_blog_path})?/docs/*", '', x.replace('\\', '/')).replace(
                        '.md', ''
                        )
                for x in iglob(str(base) + os.sep + '**', recursive = True)
                if os.path.isfile(x)
                ]
            file_found = [
                '/' + x for x in all_docs if os.path.basename(x) == file_name or x == file_name
                ]
            if file_found :
                internal_link = file_found[0]
            else :
                internal_link = file_name
    filepath = internal_link.replace(base, '')
    url = filepath.replace('\\', '/').replace('.md', '')
    url = re.sub(r'\/$', '', str(url_blog)) + '/' + quote(url)
    if not url.startswith('http') :
        url = 'https://' + url
    if not url.endswith('/') and not re.search(r'\.(.*)$', url) :
        url = url + '/'
    return url
