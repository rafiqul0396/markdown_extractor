
# Add the project root to the Python path
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from markdown_analyzer_lib.markdown_analyzer import MarkdownAnalyzer


# Path to the test markdown file
data_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'test_code.md')
# Fallback
# data_file_path = "data/test_code.md"

# The MarkdownAnalyzer class does not have a single `count_elements(element_type)` method.
# Instead, you call the specific `identify_X()` method for an element type
# and then count the results (e.g., len(analyzer.identify_headers().get("Header", []))).
# The `analyse()` method provides a summary of counts for many common elements.

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

    print("\n--- Counting Specific Element Types ---")

    # Example: Count Headers
    headers_data = analyzer.identify_headers()
    header_count = len(headers_data.get("Header", []))
    print(f"Number of Headers: {header_count}")

    # Example: Count Paragraphs
    paragraphs_data = analyzer.identify_paragraphs()
    paragraph_count = len(paragraphs_data.get("Paragraph", []))
    print(f"Number of Paragraphs: {paragraph_count}")

    # Example: Count Code Blocks
    code_blocks_data = analyzer.identify_code_blocks()
    code_block_count = len(code_blocks_data.get("Code block", []))
    print(f"Number of Code Blocks: {code_block_count}")

    # Example: Count Tables
    tables_data = analyzer.identify_tables()
    table_count = len(tables_data.get("Table", []))
    print(f"Number of Tables: {table_count}")
    
    # Example: Count Task Items
    task_items_data = analyzer.identify_task_items()
    task_item_count = len(task_items_data) # identify_task_items returns a list
    print(f"Number of Task Items: {task_item_count}")

    # For a comprehensive count of many elements, use the analyse() method
    print("\n--- Using analyse() for a summary of counts ---")
    analysis_summary = analyzer.analyse()
    print("Global Analysis Summary:")
    for key, value in analysis_summary.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")

except FileNotFoundError as fnf_error:
    print(f"Error: {fnf_error}")
    print(f"Current working directory: {os.getcwd()}")
    print("Please ensure the 'data/test_code.md' file exists in the correct location.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
