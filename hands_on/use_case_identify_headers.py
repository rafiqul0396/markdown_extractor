
import os
import sys
import json
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from markdown_analyzer_lib.markdown_analyzer import MarkdownAnalyzer
# Path to the test markdown file
# Assuming 'data' folder is at the same level as 'hands_on'
# and the script is run from the project root 'markdown_extractor'
data_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'test_code.md')
# Fallback if running directly from 'markdown_extractor'
# data_file_path = "data/test_code.md"

try:
    print(f"Attempting to load Markdown file from: {data_file_path}")
    if not os.path.exists(data_file_path):
        # Attempt fallback path if the primary one doesn't exist
        # This is useful if the script is run from 'markdown_extractor' directly
        alt_data_file_path = "data/test_code.md"
        if os.path.exists(alt_data_file_path):
            data_file_path = alt_data_file_path
            print(f"Using fallback data file path: {data_file_path}")
        else:
            raise FileNotFoundError(f"Markdown file not found at {data_file_path} or {alt_data_file_path}")

    analyzer = MarkdownAnalyzer(file_path=data_file_path)
    print("MarkdownAnalyzer initialized successfully.")

    # Use case for identify_headers()
    headers = analyzer.identify_headers()
    print("\n--- Identified Headers ---")
    if headers.get("Header"):
        print(json.dumps(headers, indent=2))
    else:
        print("No headers found or an issue with header identification.")

except FileNotFoundError as fnf_error:
    print(f"Error: {fnf_error}")
    print(f"Current working directory: {os.getcwd()}")
    print("Please ensure the 'data/test_code.md' file exists in the correct location relative to the script or project root.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
