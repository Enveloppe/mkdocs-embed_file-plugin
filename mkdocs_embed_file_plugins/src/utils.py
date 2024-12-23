import re
from bs4 import BeautifulSoup

def strip_comments(markdown):
    file_content = markdown.split("\n")
    markdown = ""
    for line in file_content:
        if (
            not re.search(r"%%(.*)%%", line)
            or not line.startswith("%%")
            or not line.endswith("%%")
        ):
            markdown += line + "\n"
    markdown = re.sub(r"%%(.*)%%", "", markdown, flags=re.DOTALL)
    return markdown


def create_link(link):
    if link.endswith("/"):
        return link[:-1] + ".md"
    else:
        return link + ".md"


def add_not_found_class(html) :
    soup = BeautifulSoup(html, "html.parser")

    for a_tag in soup.find_all("a") :
        href = a_tag.get("href", "")
        if href.startswith("notfound::") :
            clean_href = href.replace("notfound::", "")
            a_tag["href"] = clean_href
            a_tag["class"] = a_tag.get("class", []) + ["ezlinks_not_found"]
            new_tag = soup.new_tag("span")
            new_tag.string = a_tag.string
            for attr in a_tag.attrs :
                if attr != "href" :
                    new_tag[attr] = a_tag[attr]
            new_tag["src"] = clean_href
            a_tag.replaceWith(new_tag)

    return str(soup)