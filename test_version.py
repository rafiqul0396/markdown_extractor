#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify the markdown-analyzer-lib package version and functionality.
"""

import sys
import pkg_resources

# Check the package version
try:
    version = pkg_resources.get_distribution("markdown-analyzer-lib").version
    print(f"Installed markdown-analyzer-lib version: {version}")
except pkg_resources.DistributionNotFound:
    print("markdown-analyzer-lib is not installed")
    sys.exit(1)

# Import the library
from markdown_analyzer_lib import MarkdownDocument

# Test with a simple markdown string
test_markdown = """
# Test Document

This is a paragraph with **bold** and *italic* text.

## Section 1
- List item 1
- List item 2

[Link to GitHub](https://github.com/rafiqul0396/markdown_extractor)
"""

# Create a document from the string
doc = MarkdownDocument.from_string(test_markdown)

# Get a summary
summary = doc.get_summary()
print("\nDocument Summary:")
for key, value in summary.items():
    print(f"- {key.replace('_', ' ').capitalize()}: {value}")

# Check for headers
headers = doc.get_headers()
print("\nHeaders:")
for header in headers:
    print(f"- Level {header['level']}: {header['text']}")

# Check for links
links = doc.get_links()
print("\nLinks:")
for link_type, link_list in links.items():
    if link_list:
        print(f"  {link_type}:")
        for link in link_list:
            if link_type == "Text Links":
                print(f"  - Text: {link.get('text')}, URL: {link.get('url')}")
            else:
                print(f"  - Alt Text: {link.get('alt_text')}, URL: {link.get('url')}")

print("\nTest completed successfully!")
