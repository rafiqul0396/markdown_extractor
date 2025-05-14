import json
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from markdown_analyzer_lib.markdown_analyzer import MarkdownAnalyzer

# Construct the path to the data file relative to this script's location
# Assuming 'data' folder is at the same level as 'hands_on' and 'markdown_analyzer_lib_project'
# and the script is run from the project root 'markdown_extractor'
data_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'test_code.md')
# Or, if running from 'markdown_extractor' directly:
# data_file_path = "data/test_code.md"


try:
    # Use case for __init__: Load the Markdown from path
    print(f"Attempting to load Markdown file from: {data_file_path}")
    analyzer = MarkdownAnalyzer(file_path=data_file_path)
    print("MarkdownAnalyzer initialized successfully with file path.")
    print(f"Loaded content (first 100 chars): {analyzer.text[:100]}...")

    # Example of loading from a file object (using from_string)
    print("\nAttempting to load Markdown from file object...")
    with open(data_file_path, 'r', encoding='utf-8') as f:
        content_from_file_object = f.read()
        analyzer_from_string = MarkdownAnalyzer.from_string(content_from_file_object)
        print("MarkdownAnalyzer initialized successfully using from_string with content from file object.")
        print(f"Loaded content via from_string (first 100 chars): {analyzer_from_string.text[:100]}...")

except FileNotFoundError:
    print(f"Error: The file '{data_file_path}' was not found.")
    print(f"Current working directory: {os.getcwd()}")
    print("Please ensure the 'data/test_code.md' file exists in the correct location.")
except Exception as e:
    print(f"An error occurred: {e}")
