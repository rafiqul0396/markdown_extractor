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

    # Use case for identify_paragraphs()
    print("\n--- Identified Paragraphs ---")
    paragraphs_data = analyzer.identify_paragraphs()

    if paragraphs_data.get("Paragraph"):
        print(f"Found {len(paragraphs_data['Paragraph'])} paragraph(s):")
        # Printing all paragraphs might be verbose for large files,
        # so let's print the first few or a summary.
        for i, para_content in enumerate(paragraphs_data["Paragraph"][:5]): # Print first 5
            print(f"\nParagraph {i+1}:")
            print(para_content)
        if len(paragraphs_data["Paragraph"]) > 5:
            print(f"\n... and {len(paragraphs_data['Paragraph']) - 5} more paragraph(s).")
        # For a more structured output if needed:
        # print(json.dumps(paragraphs_data, indent=2))
    else:
        print("No paragraphs found or an issue with paragraph identification.")

except FileNotFoundError as fnf_error:
    print(f"Error: {fnf_error}")
    print(f"Current working directory: {os.getcwd()}")
    print("Please ensure the 'data/test_code.md' file exists in the correct location.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
