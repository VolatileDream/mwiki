
from html import HtmlRender
from index import IndexRender
from quotes import QuotesPlugin

register(HtmlRender())
register(IndexRender())
register(QuotesPlugin())
