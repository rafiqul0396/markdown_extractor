"""
Markdown Analyzer Library
=========================

A Python library for parsing, analyzing, and converting Markdown and MDX documents,
and for converting websites into structured Markdown.
"""

from .markdown_analyzer import (
    BlockToken,
    InlineParser,
    MarkdownParser,
    MarkdownAnalyzer,
    MDXMarkdownParser,
    MDXMarkdownAnalyzer,
    WebsiteScraper,
    MarkdownConverter,
    WebsiteMarkdownDocument,
    MarkdownSiteConverter,
    MarkdownDocument
)
# If mrkdwntool.py has functions/classes to be exposed directly from the library:
# from .mrkdwntool import SomeToolClassOrFunction

__version__ = "0.1.0"

__all__ = [
    "BlockToken",
    "InlineParser",
    "MarkdownParser",
    "MarkdownAnalyzer",
    "MDXMarkdownParser",
    "MDXMarkdownAnalyzer",
    "WebsiteScraper",
    "MarkdownConverter",
    "WebsiteMarkdownDocument",
    "MarkdownSiteConverter",
    "MarkdownDocument",
    # "SomeToolClassOrFunction", # Add if imported from mrkdwntool.py
    "__version__",
]
