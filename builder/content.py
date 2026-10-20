"""Text transformations shared by the server and static Wiki renderer."""
from html import escape
from html.parser import HTMLParser
import re

import markdown


class KeywordHighlighter(HTMLParser):
    # Never change markup, URLs, author-supplied emphasis or code examples.
    SKIP = {"a", "strong", "b", "code", "pre", "script", "style", "textarea",
            "svg", "h1", "h2", "h3", "h4", "h5", "h6"}
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, keywords: list[str]):
        super().__init__(convert_charrefs=False)
        self.pattern = re.compile("|".join(re.escape(word) for word in
                                         sorted(set(keywords), key=len, reverse=True)))
        self.stack: list[str] = []
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        self.parts.append(self.get_starttag_text())
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.parts.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        self.parts.append(f"</{tag}>")
        if tag in self.stack:
            del self.stack[len(self.stack) - 1 - self.stack[::-1].index(tag):]

    def handle_data(self, data):
        if not self.SKIP.intersection(self.stack):
            data = self.pattern.sub(
                lambda match: f'<strong class="person-keyword">{escape(match.group())}</strong>', data)
        self.parts.append(data)

    def handle_entityref(self, name):
        self.parts.append(f"&{name};")

    def handle_charref(self, name):
        self.parts.append(f"&#{name};")

    def handle_comment(self, data):
        self.parts.append(f"<!--{data}-->")

    def handle_decl(self, decl):
        self.parts.append(f"<!{decl}>")


def highlight_keywords(html: str, keywords: list[str]) -> str:
    if not keywords:
        return html
    parser = KeywordHighlighter(keywords)
    parser.feed(html)
    parser.close()
    return "".join(parser.parts)


def biography_parts(text: str, default_title: str) -> tuple[str, str, str]:
    """Read an optional Markdown meta block, then an opening ATX title."""
    text = text.removeprefix("\ufeff").replace("\r\n", "\n")
    author = ""
    metadata = re.match(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|$)", text, re.DOTALL)
    if metadata:
        reader = markdown.Markdown(extensions=["meta"])
        reader.convert(metadata.group(1) + "\n\n")
        author = " ".join(reader.Meta.get("author", [])).strip()
        # The metadata block supports a plain-text author, with optional quotes.
        if len(author) >= 2 and author[0] == author[-1] and author[0] in "\"'":
            author = author[1:-1]
        text = text[metadata.end():]
    text = text.lstrip("\n")
    heading = re.match(r"\A {0,3}#[ \t]+([^\n]+)(?:\n|$)", text)
    title = default_title
    if heading:
        title = re.sub(r"[ \t]+#+[ \t]*$", "", heading.group(1)).strip()
        text = text[heading.end():].lstrip("\n")
    return title, author, text
