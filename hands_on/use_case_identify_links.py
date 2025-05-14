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

    # Use case for identify_links()
    print("\n--- Identified Links (Text and Image) ---")
    links_data = analyzer.identify_links()

    if links_data:
        if links_data.get("Text Links"):
            print(f"\nFound {len(links_data['Text Links'])} text link(s):")
            for i, link_info in enumerate(links_data["Text Links"]):
                print(f"  Text Link {i+1}:")
                print(f"    Line: {link_info.get('line')}")
                print(f"    Text: {link_info.get('text')}")
                print(f"    URL: {link_info.get('url')}")
                if 'context' in link_info:
                    print(f"    Context: {link_info.get('context')}")
        else:
            print("\nNo text links found.")

        if links_data.get("Image Links"):
            print(f"\nFound {len(links_data['Image Links'])} image link(s):")
            for i, img_info in enumerate(links_data["Image Links"]):
                print(f"  Image Link {i+1}:")
                print(f"    Line: {img_info.get('line')}")
                print(f"    Alt Text: {img_info.get('alt_text')}")
                print(f"    URL: {img_info.get('url')}")
                if 'context' in img_info:
                    print(f"    Context: {img_info.get('context')}")
        else:
            print("\nNo image links found.")
        
        # For a more structured JSON output if needed:
        # print("\nFull JSON output for links:")
        # print(json.dumps(links_data, indent=2))
    else:
        print("No links (text or image) found or an issue with link identification.")
        print("Ensure 'test_code.md' contains Markdown links, e.g.:")
        print("  [Example Link](http://example.com)")
        print("  ![Example Image](http://example.com/image.png)")
        print("  [Reference Link][ref]")
        print("  [ref]: http://example.com/ref")

except FileNotFoundError as fnf_error:
    print(f"Error: {fnf_error}")
    print(f"Current working directory: {os.getcwd()}")
    print("Please ensure the 'data/test_code.md' file exists in the correct location.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
