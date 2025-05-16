# Markdown Analyzer Library

A Python library for parsing, analyzing, and converting Markdown and MDX documents. It also includes capabilities to scrape websites and convert their content into structured Markdown.

## Features

-   Parse Markdown and MDX into an Abstract Syntax Tree (AST)-like structure.
-   Identify various Markdown elements: headers, paragraphs, lists, code blocks, tables, links, footnotes, etc.
-   Analyze document statistics: word count, character count, element counts.
-   Convert HTML content to Markdown.
-   Scrape websites and convert entire sites into a single Markdown document.
-   Basic MDX parsing support.

## Installation

```bash
pip install markdown-analyzer-lib
```
(Once published to PyPI)

To install locally for development:
```bash
# Navigate to the markdown_analyzer_lib_project directory
pip install .
# or for an editable install
pip install -e .
```

## User Documentation

This section provides detailed information on how to use the Markdown Analyzer Library.

### Running the Library

The Markdown Analyzer Library is designed to be used as a Python library integrated into your own Python scripts or applications.

#### As a Python Library

To use the library, you first need to import the relevant classes. The primary classes are `MarkdownDocument` for handling individual Markdown files or strings, and `MarkdownSiteConverter` for converting websites.

**1. Analyzing a Local Markdown File:**

You can parse and analyze a Markdown file directly from your file system.

```python
from markdown_analyzer_lib import MarkdownDocument

# Create a MarkdownDocument object from a file
try:
    doc = MarkdownDocument.from_file("path/to/your/document.md")
except FileNotFoundError:
    print("Error: The specified file was not found.")
    exit()
except Exception as e:
    print(f"An error occurred: {e}")
    exit()

# Get a summary of the document
# Includes word count, character count, and counts of various elements
summary = doc.get_summary()
print("Document Summary:")
for key, value in summary.items():
    print(f"- {key.replace('_', ' ').capitalize()}: {value}")

# Get all headers
headers = doc.get_headers()
print("\nHeaders:")
if headers:
    for header in headers:
        print(f"- Level {header['level']}: {header['text']} (Line {header['line']})")
else:
    print("No headers found.")

# Get all paragraphs
paragraphs = doc.get_paragraphs()
print("\nParagraphs:")
if paragraphs:
    for i, para_content in enumerate(paragraphs): # para_content is a string
        # Note: get_paragraphs() returns a list of content strings.
        # For line numbers, you might need to use get_sequential_elements() or analyze tokens.
        print(f"Para {i+1}: {para_content[:100]}...") # Print first 100 chars
else:
    print("No paragraphs found.")

# Get all links
links_data = doc.get_links() # Returns a dictionary with "Text Links" and "Image Links" keys
print("\nLinks:")
if links_data:
    # links_data is a dictionary, e.g., {"Text Links": [...], "Image Links": [...]}
    # Iterate through all link types and then all links of that type
    for link_type, link_list in links_data.items():
        print(f"  {link_type}:")
        if link_list:
            for link_detail in link_list:
                if link_type == "Text Links":
                    print(f"  - Text: {link_detail.get('text', 'N/A')}, URL: {link_detail['url']} (Line {link_detail.get('line', 'N/A')})")
                else: # Image Links
                    print(f"  - Alt Text: {link_detail.get('alt_text', 'N/A')}, URL: {link_detail['url']} (Line {link_detail.get('line', 'N/A')})")
        else:
            print("    No links of this type found.")
else:
    print("No links found.")

# Get all code blocks
code_blocks = doc.get_code_blocks()
print("\nCode Blocks:")
if code_blocks:
    for i, block in enumerate(code_blocks):
        lang = block.get('language', 'N/A')
        # Use 'start_line' for line number and 'content' for code text
        print(f"Block {i+1} (Language: {lang}, Line {block.get('start_line', 'N/A')}):")
        code_content = block.get('content', '')
        print(code_content[:150] + "..." if len(code_content) > 150 else code_content)
else:
    print("No code blocks found.")

# Get sequential elements (for advanced use)
# seq_elements = doc.get_sequential_elements()
# print("\nSequential Elements (excerpt):")
# print(str(seq_elements[:3]))
```

**2. Analyzing Markdown from a String:**

If you have Markdown content as a string, you can parse it directly.

```python
from markdown_analyzer_lib import MarkdownDocument

markdown_string = """
# My Document Title
This is the first paragraph. It contains some *italic* and **bold** text.

## Section 1
- List item 1
- List item 2

Another paragraph here.
"""
doc_from_string = MarkdownDocument.from_string(markdown_string)

print("Summary from String:")
summary = doc_from_string.get_summary()
for key, value in summary.items():
    print(f"- {key.replace('_', ' ').capitalize()}: {value}")

print("\nHeaders from String:")
headers = doc_from_string.get_headers()
for header in headers:
    print(f"- Level {header['level']}: {header['text']}")
```

**3. Converting a Website to Markdown:**

The library can scrape a website and convert its content into a single Markdown document. This is useful for archiving web content or analyzing website structure.

*Note: Web scraping should be done responsibly and in compliance with the website's `robots.txt` and terms of service.*

```python
from markdown_analyzer_lib import MarkdownSiteConverter

# Initialize the converter with the base URL of the site you want to scrape
# max_depth controls how many levels of links to follow from the base URL
# output_file is where the combined Markdown content will be saved
# Be cautious with max_depth, as it can lead to very large outputs and long processing times.
# Start with max_depth=0 (only the base URL) or max_depth=1.

# Example (commented out to prevent accidental execution during tests):
# try:
#     site_converter = MarkdownSiteConverter(
#         base_url="https://example.com", # Replace with a real, simple site for testing
#         max_depth=0, # Only scrape the initial page
#         output_file="website_content.md"
#     )
#     print(f"Starting website conversion for {site_converter.base_url}...")
#     markdown_output_path = site_converter.convert_site_to_markdown()
#     if markdown_output_path:
#         print(f"Website converted and saved to: {markdown_output_path}")
#         # You can then analyze this generated Markdown file:
#         # site_doc = MarkdownDocument.from_file(markdown_output_path)
#         # print("\nSummary of scraped website content:")
#         # print(site_doc.get_summary())
#     else:
#         print("Website conversion failed or produced no output.")
# except Exception as e:
#     print(f"An error occurred during website conversion: {e}")

# For a practical example, ensure you have a test website or use a simple, permissive one.
# For instance, if you have a local server running at http://localhost:8000 with some HTML files:
# site_converter_local = MarkdownSiteConverter(
# base_url="http://localhost:8000",
# max_depth=1,
# output_file="local_site_content.md"
# )
# local_site_markdown = site_converter_local.convert_site_to_markdown()
# if local_site_markdown:
# print(f"Local site converted to {local_site_markdown}")
```

### User Manual

This manual provides guidance on how to effectively use the library for common tasks.

**Task 1: Getting Document Statistics**
Use the `get_summary()` method on a `MarkdownDocument` object.

```python
doc = MarkdownDocument.from_file("my_document.md")
summary = doc.get_summary()
print(f"Word Count: {summary['words']}") 
print(f"Character Count: {summary['characters']}") 
print(f"Paragraph Count: {summary['paragraphs']}") 
```

**Task 2: Extracting All Links from a Document**
Use the `get_links()` method.

```python
doc = MarkdownDocument.from_file("my_document.md")
links_data = doc.get_links() # Returns a dictionary with "Text Links" and "Image Links" keys
if links_data:
    # links_data is a dictionary, e.g., {"Text Links": [...], "Image Links": [...]}
    # Iterate through all link types and then all links of that type
    for link_type, link_list in links_data.items():
        print(f"  {link_type}:")
        if link_list:
            for link_detail in link_list:
                if link_type == "Text Links":
                    print(f"  - Text: {link_detail.get('text', 'N/A')}, URL: {link_detail['url']} (Line {link_detail.get('line', 'N/A')})")
                else: # Image Links
                    print(f"  - Alt Text: {link_detail.get('alt_text', 'N/A')}, URL: {link_detail['url']} (Line {link_detail.get('line', 'N/A')})")
        else:
            print("    No links of this type found.")
else:
    print("No links found.")
```

**Task 3: Finding Specific Headers**
Iterate through the results of `get_headers()` and filter by level or text.

```python
doc = MarkdownDocument.from_file("my_document.md")
h2_headers = [h for h in doc.get_headers() if h['level'] == 2]
print("All H2 Headers:")
for h2 in h2_headers:
    print(f"- {h2['text']}")
```

**Task 4: Converting an Online Article to Markdown for Offline Reading**
Use `MarkdownSiteConverter` with `max_depth=0` pointing to the article's URL.

```python
from markdown_analyzer_lib import MarkdownSiteConverter
# article_converter = MarkdownSiteConverter(
#     base_url="URL_OF_THE_ARTICLE_HERE",
#     max_depth=0
# )
# article_converter.convert_site_to_markdown(output_file="article.md")
# print("Article saved to article.md")
```

### API Reference (To Be Expanded)

Detailed API documentation for all classes and methods will be available [here](LINK_TO_API_DOCS_OR_WIKI) or can be generated using tools like Sphinx. For now, please refer to the source code docstrings for detailed information on parameters and return values.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
