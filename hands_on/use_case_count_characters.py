

import os
import sys
# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# Path to the test markdown file
data_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'test_code.md')
# Fallback
data_file_path = "data/test_code.md"
from markdown_analyzer_lib.markdown_analyzer import MarkdownAnalyzer

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

    # Use case for count_characters()
    print("\n--- Counting Non-Whitespace Characters ---")
    char_count = analyzer.count_characters()
    print(f"Total non-whitespace characters in the document: {char_count}")

    # For context, let's show a snippet of the text
    print(f"\nDocument snippet (first 200 chars):")
    print(analyzer.text[:200] + "..." if len(analyzer.text) > 200 else analyzer.text)
    print(f"\nTotal characters including whitespace (len(analyzer.text)): {len(analyzer.text)}")


except FileNotFoundError as fnf_error:
    print(f"Error: {fnf_error}")
    print(f"Current working directory: {os.getcwd()}")
    print("Please ensure the 'data/test_code.md' file exists in the correct location.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
