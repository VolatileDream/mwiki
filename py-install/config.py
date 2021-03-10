
from events import EventsPlugin
from html import HtmlRender
from index import IndexRender
from mentions import MentionsPlugin
from missing import MissingPlugin
from quotes import QuotesPlugin

register(EventsPlugin())
register(HtmlRender())
register(IndexRender())
register(MissingPlugin())
register(MentionsPlugin())
register(QuotesPlugin())
