import os
import json
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from markdown_analyzer_lib.markdown_analyzer import MarkdownAnalyzer, MarkdownDocument
# Create a MarkdownDocument object from a file
try:
    doc = MarkdownDocument.from_file("C:/Users/rafiqul.islam/Desktop/markdown_extractor/markdown_analyzer_lib_project\data/13529199_prapti_haskos.md")
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
print(f"Total Paragraphs: {len(paragraphs)}")
print("Excerpt of first paragraph:")
print(paragraphs[0] + "...")  # Print first 100 characters of the first paragraph


# Get all links
links = doc.get_links()
print("\nLinks:")
print(f"Total Links: {len(links)}")

# Get all code blocks
code_blocks = doc.get_code_blocks()
print("\nCode Blocks:")
print(f"Total Code Blocks: {len(code_blocks)}")

# Get raw AST-like structure (for advanced use)
# ast_structure = doc.get_ast()
# print("\nAST Structure (excerpt):")
# print(str(ast_structure)[:500] + "...")
# get tables