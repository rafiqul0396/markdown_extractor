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

# The MarkdownAnalyzer class does not have a dedicated `identify_sections()` method
# for Setext-style headers specifically after the initial parsing phase.
# Setext headers (H1 with ===, H2 with ---) are parsed into 'header' tokens
# by the `MarkdownParser` class, similar to ATX headers.
# The `identify_headers()` method will return all headers regardless of their original syntax (ATX or Setext).

# This use case will demonstrate identifying all headers.
# The `test_code.md` file should contain examples of Setext headers for this to be meaningful.
# Example Setext H1:
# Section Title
# =============
# Example Setext H2:
# Subsection Title
# ---------------

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

    # Setext sections are identified as 'header' tokens.
    # We use identify_headers() to get them.
    # The `level` attribute will be 1 for H1 (===) and 2 for H2 (---).
    print("\n--- Identifying All Headers (ATX and Setext are tokenized as 'header') ---")
    headers_data = analyzer.identify_headers()

    if headers_data.get("Header"):
        print("All identified headers:")
        print(json.dumps(headers_data, indent=2))
        
        # Note: The current parser (MarkdownParser) tokenizes both ATX and Setext headers
        # into a generic 'header' token with a 'level'. It does not store a flag
        # indicating "this was originally a Setext header".
        # To specifically identify Setext-originated headers, the MarkdownParser
        # would need to be modified to add such metadata to the BlockToken.
        # For now, we can only see all headers.
        print("\nNote: Setext headers are included above as 'header' tokens with appropriate levels.")
        print("The parser does not currently distinguish their origin (ATX vs Setext) in the final token's metadata.")
    else:
        print("No headers found or an issue with header identification.")

except FileNotFoundError as fnf_error:
    print(f"Error: {fnf_error}")
    print(f"Current working directory: {os.getcwd()}")
    print("Please ensure the 'data/test_code.md' file exists in the correct location relative to the script or project root.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
