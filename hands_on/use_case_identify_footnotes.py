
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

    # Use case for identify_footnotes()
    # This method returns footnote definitions and their usage.
    print("\n--- Identified Footnotes (Definitions and Usage) ---")
    footnotes_data = analyzer.identify_footnotes() # This returns a list of dicts

    if footnotes_data:
        print(f"Found {len(footnotes_data)} footnote reference(s)/definition(s) used in the document:")
        # The identify_footnotes method in the analyzer appears to return a list of
        # footnote usages, including their content if resolved.
        # The parser also separately collects all footnote definitions in `analyzer.footnotes`.

        print("\nFootnote Definitions (from analyzer.footnotes):")
        if analyzer.footnotes:
            for fn_id, fn_content in analyzer.footnotes.items():
                print(f"  ID [^{fn_id}]: {fn_content}")
        else:
            print("  No raw footnote definitions found by the parser in analyzer.footnotes.")

        print("\nFootnote Usage Details (from identify_footnotes()):")
        for i, fn_info in enumerate(footnotes_data):
            print(f"  Footnote Usage {i+1}:")
            print(f"    Line of usage: {fn_info.get('line')}")
            print(f"    ID: {fn_info.get('id')}")
            print(f"    Content: {fn_info.get('content')}")
        
        # For a more structured JSON output if needed:
        # print("\nFull JSON output for identified footnote usages:")
        # print(json.dumps(footnotes_data, indent=2))
    else:
        print("No footnotes found or an issue with footnote identification.")
        print("Ensure 'test_code.md' contains footnote definitions and references, e.g.:")
        print("  Here is some text with a footnote.[^1]")
        print("  [^1]: This is the footnote definition.")

except FileNotFoundError as fnf_error:
    print(f"Error: {fnf_error}")
    print(f"Current working directory: {os.getcwd()}")
    print("Please ensure the 'data/test_code.md' file exists in the correct location.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
