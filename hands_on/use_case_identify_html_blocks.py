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

    # Use case for identify_html_blocks()
    print("\n--- Identified HTML Blocks ---")
    html_blocks_data = analyzer.identify_html_blocks() # Returns a list of dicts

    if html_blocks_data:
        print(f"Found {len(html_blocks_data)} HTML block(s):")
        for i, block_info in enumerate(html_blocks_data):
            print(f"\nHTML Block {i+1}:")
            print(f"  Line: {block_info.get('line')}")
            print(f"  Content:\n{block_info.get('content')}")
        
        # For a more structured JSON output if needed:
        # print("\nFull JSON output for HTML blocks:")
        # print(json.dumps(html_blocks_data, indent=2))
    else:
        print("No HTML blocks found or an issue with HTML block identification.")
        print("Ensure 'test_code.md' contains block-level HTML tags, e.g.:")
        print("  <div>\n    <p>This is an HTML block.</p>\n  </div>")
        print("  <!-- This is an HTML comment block -->")

except FileNotFoundError as fnf_error:
    print(f"Error: {fnf_error}")
    print(f"Current working directory: {os.getcwd()}")
    print("Please ensure the 'data/test_code.md' file exists in the correct location.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
