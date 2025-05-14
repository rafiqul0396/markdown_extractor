import json
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from markdown_analyzer_lib.markdown_analyzer import MarkdownAnalyzer


# Path to the test markdown file
data_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'test_code.md')
# Fallback
# data_file_path = "data/test_code.md"

try:
    print(f"Attempting to load Markdown file from: {data_file_path}")
    if not os.path.exists(data_file_path):
        alt_data_file_path = "data/test_code.md"
        if os.path.exists(alt_data_file_path):
            data_file_path = alt_data_file_path
            print(f"Using fallback data file path: {data_file_path}")
        else:
            raise FileNotFoundError(f"Markdown file not found at {data_file_path} or {alt_data_file_path}")

    analyzer = MarkdownAnalyzer(file_path=data_file_path)
    print("MarkdownAnalyzer initialized successfully.")

    # Use case for identify_html_inline()
    print("\n--- Identified Inline HTML Elements ---")
    inline_html_data = analyzer.identify_html_inline() # Returns a list of dicts

    if inline_html_data:
        print(f"Found {len(inline_html_data)} inline HTML element(s):")
        for i, html_info in enumerate(inline_html_data):
            print(f"\nInline HTML {i+1}:")
            print(f"  Line: {html_info.get('line')}")
            print(f"  HTML: {html_info.get('html')}")
        
        # For a more structured JSON output if needed:
        # print("\nFull JSON output for inline HTML:")
        # print(json.dumps(inline_html_data, indent=2))
    else:
        print("No inline HTML elements found or an issue with identification.")
        print("Ensure 'test_code.md' contains inline HTML tags, e.g.:")
        print("  This is text with an <small>inline HTML</small> element or a <br/> tag.")

except FileNotFoundError as fnf_error:
    print(f"Error: {fnf_error}")
    print(f"Current working directory: {os.getcwd()}")
    print("Please ensure the 'data/test_code.md' file exists in the correct location.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
