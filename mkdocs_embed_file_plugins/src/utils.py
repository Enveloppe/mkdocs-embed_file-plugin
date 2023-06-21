import re


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
