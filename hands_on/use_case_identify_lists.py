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

    # Use case for identify_lists()
    print("\n--- Identified Lists (Ordered and Unordered, including Tasks) ---")
    lists_data = analyzer.identify_lists()

    if lists_data.get("Ordered list") or lists_data.get("Unordered list"):
        if lists_data.get("Ordered list"):
            print(f"\nFound {len(lists_data['Ordered list'])} ordered list(s):")
            for i, ol_items in enumerate(lists_data["Ordered list"]):
                print(f"  Ordered List {i+1}:")
                for item_idx, item in enumerate(ol_items):
                    task_status = ""
                    if item.get("task_item"):
                        task_status = "[x] " if item.get("checked") else "[ ] "
                    print(f"    {item_idx + 1}. {task_status}{item.get('text')}")
        
        if lists_data.get("Unordered list"):
            print(f"\nFound {len(lists_data['Unordered list'])} unordered list(s):")
            for i, ul_items in enumerate(lists_data["Unordered list"]):
                print(f"  Unordered List {i+1}:")
                for item_idx, item in enumerate(ul_items):
                    task_status = ""
                    if item.get("task_item"):
                        task_status = "[x] " if item.get("checked") else "[ ] "
                    print(f"    - {task_status}{item.get('text')}")
        
        # For a more structured output if needed:
        # print("\nFull JSON output for lists:")
        # print(json.dumps(lists_data, indent=2))
    else:
        print("No lists found or an issue with list identification.")
        print("Ensure 'test_code.md' contains ordered (e.g., 1. Item), unordered (e.g., - Item), or task lists (e.g., - [ ] Task).")

except FileNotFoundError as fnf_error:
    print(f"Error: {fnf_error}")
    print(f"Current working directory: {os.getcwd()}")
    print("Please ensure the 'data/test_code.md' file exists in the correct location.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
