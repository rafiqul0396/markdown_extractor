from markdown_analyzer_lib import MarkdownDocument

# Create a MarkdownDocument object from a file
try:
    doc = MarkdownDocument.from_file("C:/Users/rafiqul.islam/Desktop/markdown_extractor/markdown_analyzer_lib_project\data/13529199_prapti_haskos.md")
except FileNotFoundError:
    print("Error: The specified file was not found.")
    exit()
except Exception as e:
    print(f"An error occurred: {e}")
    exit()

# Get a summary of the document
# Includes word count, character count, and counts of various elements
summary = doc.get_summary()
print("Document Summary:")
for key, value in summary.items():
    print(f"- {key.replace('_', ' ').capitalize()}: {value}")

# Get all headers
headers = doc.get_headers()
print("\nHeaders:")
if headers:
    for header in headers:
        print(f"- Level {header['level']}: {header['text']} (Line {header['line']})")
else:
    print("No headers found.")

# Get all paragraphs
paragraphs = doc.get_paragraphs()
print("\nParagraphs:")
if paragraphs:
    for i, para_content in enumerate(paragraphs): # para_content is a string
        # Note: get_paragraphs() returns a list of content strings.
        # For line numbers, you might need to use get_sequential_elements() or analyze tokens.
        print(f"Para {i+1}: {para_content[:100]}...") # Print first 100 chars
else:
    print("No paragraphs found.")

# Get all links
links_data = doc.get_links() # Returns a dictionary with "Text Links" and "Image Links" keys
print("\nLinks:")
if links_data:
    # links_data is a dictionary, e.g., {"Text Links": [...], "Image Links": [...]}
    # Iterate through all link types and then all links of that type
    for link_type, link_list in links_data.items():
        print(f"  {link_type}:")
        if link_list:
            for link_detail in link_list:
                if link_type == "Text Links":
                    print(f"  - Text: {link_detail.get('text', 'N/A')}, URL: {link_detail['url']} (Line {link_detail.get('line', 'N/A')})")
                else: # Image Links
                    print(f"  - Alt Text: {link_detail.get('alt_text', 'N/A')}, URL: {link_detail['url']} (Line {link_detail.get('line', 'N/A')})")
        else:
            print("    No links of this type found.")
else:
    print("No links found.")

# Get all code blocks
code_blocks = doc.get_code_blocks()
print("\nCode Blocks:")
if code_blocks:
    for i, block in enumerate(code_blocks):
        lang = block.get('language', 'N/A')
        # Use 'start_line' for line number and 'content' for code text
        print(f"Block {i+1} (Language: {lang}, Line {block.get('start_line', 'N/A')}):")
        code_content = block.get('content', '')
        print(code_content[:150] + "..." if len(code_content) > 150 else code_content)
else:
    print("No code blocks found.")