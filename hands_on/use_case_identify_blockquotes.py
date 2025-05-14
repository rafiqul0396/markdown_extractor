
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

    # Use case for identify_blockquotes()
    print("\n--- Identified Blockquotes ---")
    blockquotes_data = analyzer.identify_blockquotes()

    if blockquotes_data.get("Blockquote"):
        print(f"Found {len(blockquotes_data['Blockquote'])} blockquote(s):")
        for i, bq_content in enumerate(blockquotes_data["Blockquote"]):
            print(f"\nBlockquote {i+1}:")
            print(bq_content)
        # For a more structured output if needed:
        # print(json.dumps(blockquotes_data, indent=2))
    else:
        print("No blockquotes found or an issue with blockquote identification.")
        print("Ensure your 'test_code.md' contains blockquotes (e.g., '> This is a quote').")

except FileNotFoundError as fnf_error:
    print(f"Error: {fnf_error}")
    print(f"Current working directory: {os.getcwd()}")
    print("Please ensure the 'data/test_code.md' file exists in the correct location.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
