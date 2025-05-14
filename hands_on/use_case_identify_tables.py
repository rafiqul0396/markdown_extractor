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

    # Use case for identify_tables()
    print("\n--- Identified GFM Tables ---")
    tables_data = analyzer.identify_tables()

    if tables_data.get("Table"):
        print(f"Found {len(tables_data['Table'])} table(s):")
        for i, table_info in enumerate(tables_data["Table"]):
            print(f"\nTable {i+1}:")
            header = table_info.get('header', [])
            rows = table_info.get('rows', [])
            if header:
                print(f"  Header: | {' | '.join(header)} |")
                # Print separator line based on header columns
                separator = [":---:"] * len(header) # Common GFM alignment syntax
                print(f"  Separator: | {' | '.join(separator)} |")
            if rows:
                print("  Rows:")
                for row_idx, row_cells in enumerate(rows):
                    print(f"    | {' | '.join(row_cells)} |")
        
        # For a more structured JSON output if needed:
        # print("\nFull JSON output for tables:")
        # print(json.dumps(tables_data, indent=2))
    else:
        print("No GFM tables found or an issue with table identification.")
        print("Ensure 'test_code.md' contains GFM-style tables, e.g.:")
        print("| Header 1 | Header 2 |")
        print("| :------- | :------- |")
        print("| Cell 1   | Cell 2   |")

except FileNotFoundError as fnf_error:
    print(f"Error: {fnf_error}")
    print(f"Current working directory: {os.getcwd()}")
    print("Please ensure the 'data/test_code.md' file exists in the correct location.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
