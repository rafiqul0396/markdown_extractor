import unittest
import os
import json
from unittest.mock import patch, mock_open, MagicMock

# Assuming markdown_analyzer.py is in the parent directory of 'test' or accessible via PYTHONPATH
# Adjust the import path as necessary if your project structure is different.
# For example, if 'mrkdwn_analysis' is a package:
from markdown_analyzer_lib.markdown_analyzer import ( # Updated import path
    BlockToken,
    InlineParser,
    MarkdownParser,
    MarkdownAnalyzer,
    MDXMarkdownParser,
    MDXMarkdownAnalyzer,
    WebsiteScraper,
    MarkdownConverter,
    WebsiteMarkdownDocument,
    MarkdownSiteConverter,
    MarkdownDocument
)

# Helper function to create a temporary markdown file
def create_temp_md_file(filename="temp_test_file.md", content=""):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename

# Helper function to remove a temporary file
def remove_temp_file(filename):
    if os.path.exists(filename):
        os.remove(filename)

class TestBlockToken(unittest.TestCase):
    def test_block_token_creation_defaults(self):
        token = BlockToken("paragraph", "Hello world")
        self.assertEqual(token.type, "paragraph")
        self.assertEqual(token.content, "Hello world")
        self.assertIsNone(token.level)
        self.assertEqual(token.meta, {})
        self.assertIsNone(token.line)

    def test_block_token_creation_with_all_args(self):
        token = BlockToken("header", "Title", level=1, meta={"id": "title"}, line=5)
        self.assertEqual(token.type, "header")
        self.assertEqual(token.content, "Title")
        self.assertEqual(token.level, 1)
        self.assertEqual(token.meta, {"id": "title"})
        self.assertEqual(token.line, 5)

class TestInlineParser(unittest.TestCase):
    def setUp(self):
        self.references = {"ref": "http://example.com/ref"}
        self.footnotes = {"fn1": "This is a footnote."}
        self.parser = InlineParser(references=self.references, footnotes=self.footnotes)

    def test_parse_inline_links_and_images(self):
        text = "A [link](http://example.com) and an ![image](http://example.com/img.png) and a [reference][ref]."
        result = self.parser.parse_inline(text)
        self.assertEqual(len(result["text_links"]), 2)
        self.assertEqual(result["text_links"][0], {"text": "link", "url": "http://example.com"})
        self.assertEqual(result["text_links"][1], {"text": "reference", "url": "http://example.com/ref"})
        self.assertEqual(len(result["image_links"]), 1)
        self.assertEqual(result["image_links"][0], {"alt_text": "image", "url": "http://example.com/img.png"})

    def test_parse_inline_code(self):
        text = "Some `inline code` and more `code`."
        result = self.parser.parse_inline(text)
        self.assertEqual(len(result["inline_code"]), 2)
        self.assertEqual(result["inline_code"][0], "inline code")
        self.assertEqual(result["inline_code"][1], "code")

    def test_parse_emphasis(self):
        text = "*italic*, _italic_, **bold**, __bold__"
        result = self.parser.parse_inline(text)
        self.assertEqual(len(result["emphasis"]), 4)
        self.assertIn("italic", result["emphasis"])
        self.assertIn("bold", result["emphasis"])

    def test_parse_footnotes_used(self):
        text = "This is a footnote reference [^fn1]."
        result = self.parser.parse_inline(text)
        self.assertEqual(len(result["footnotes_used"]), 1)
        self.assertEqual(result["footnotes_used"][0], {"id": "fn1", "content": "This is a footnote."})

    def test_parse_inline_html(self):
        text = "Text with <br> and <span>content</span>."
        result = self.parser.parse_inline(text)
        # BeautifulSoup might parse differently, check for presence
        self.assertTrue(any("<br/>" in h or "<br>" in h for h in result["html_inline"])) 
        self.assertTrue(any("<span>content</span>" in h for h in result["html_inline"]))


class TestMarkdownParser(unittest.TestCase):
    def test_parse_atx_header(self):
        parser = MarkdownParser("# Header 1\n## Header 2")
        tokens = parser.parse()
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[0].type, "header")
        self.assertEqual(tokens[0].content, "Header 1")
        self.assertEqual(tokens[0].level, 1)
        self.assertEqual(tokens[1].type, "header")
        self.assertEqual(tokens[1].content, "Header 2")
        self.assertEqual(tokens[1].level, 2)

    def test_parse_setext_header(self):
        parser = MarkdownParser("Header 1\n===\nHeader 2\n---")
        tokens = parser.parse()
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[0].type, "header")
        self.assertEqual(tokens[0].content, "Header 1")
        self.assertEqual(tokens[0].level, 1)
        self.assertEqual(tokens[1].type, "header")
        self.assertEqual(tokens[1].content, "Header 2")
        self.assertEqual(tokens[1].level, 2)

    def test_parse_fenced_code_block(self):
        md_text = "```python\nprint('hello')\n```"
        parser = MarkdownParser(md_text)
        tokens = parser.parse()
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].type, "code")
        self.assertEqual(tokens[0].content, "print('hello')")
        self.assertEqual(tokens[0].meta["language"], "python")

    def test_parse_indented_code_block(self):
        md_text = "    print('indented')"
        parser = MarkdownParser(md_text)
        tokens = parser.parse()
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].type, "code")
        self.assertEqual(tokens[0].content, "print('indented')")
        self.assertIsNone(tokens[0].meta["language"])
        self.assertEqual(tokens[0].meta["code_type"], "indented")


    def test_parse_blockquote(self):
        parser = MarkdownParser("> This is a quote\n> Continued quote")
        tokens = parser.parse()
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].type, "blockquote")
        self.assertEqual(tokens[0].content, "This is a quote\nContinued quote")

    def test_parse_ordered_list(self):
        parser = MarkdownParser("1. Item 1\n2. Item 2")
        tokens = parser.parse()
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].type, "ordered_list")
        self.assertEqual(len(tokens[0].meta["items"]), 2)
        self.assertEqual(tokens[0].meta["items"][0]["text"], "Item 1")

    def test_parse_unordered_list(self):
        parser = MarkdownParser("* Item A\n- Item B")
        tokens = parser.parse()
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].type, "unordered_list")
        self.assertEqual(len(tokens[0].meta["items"]), 2)
        self.assertEqual(tokens[0].meta["items"][0]["text"], "Item A")

    def test_parse_task_list(self):
        md_text = "- [x] Done\n- [ ] Not done"
        parser = MarkdownParser(md_text)
        tokens = parser.parse()
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].type, "unordered_list")
        items = tokens[0].meta["items"]
        self.assertEqual(len(items), 2)
        self.assertTrue(items[0]["task_item"])
        self.assertTrue(items[0]["checked"])
        self.assertEqual(items[0]["text"], "Done")
        self.assertTrue(items[1]["task_item"])
        self.assertFalse(items[1]["checked"])
        self.assertEqual(items[1]["text"], "Not done")

    def test_parse_hr(self):
        parser = MarkdownParser("***")
        tokens = parser.parse()
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].type, "hr")

    def test_parse_table(self):
        md_text = "| Header 1 | Header 2 |\n|---|---|\n| Cell 1 | Cell 2 |"
        parser = MarkdownParser(md_text)
        tokens = parser.parse()
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].type, "table")
        self.assertEqual(tokens[0].meta["header"], ["Header 1", "Header 2"])
        self.assertEqual(tokens[0].meta["rows"], [["Cell 1", "Cell 2"]])

    def test_parse_frontmatter(self):
        md_text = "---\ntitle: Test\n---\nContent"
        parser = MarkdownParser(md_text)
        tokens = parser.parse()
        self.assertEqual(tokens[0].type, "frontmatter")
        self.assertEqual(tokens[0].content, "title: Test")
        self.assertEqual(tokens[1].type, "paragraph") 
        self.assertEqual(tokens[1].content, "Content")

    def test_extract_references_and_footnotes(self):
        md_text = "[ref]: http://example.com\n[^fn]: Footnote content"
        parser = MarkdownParser(md_text)
        self.assertIn("ref", parser.references)
        self.assertEqual(parser.references["ref"], "http://example.com")
        self.assertIn("fn", parser.footnotes)
        self.assertEqual(parser.footnotes["fn"], "Footnote content")

    def test_parse_html_block(self):
        md_text = "<div>\n  <p>Hello</p>\n</div>\n<!-- comment -->"
        parser = MarkdownParser(md_text)
        tokens = parser.parse()
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[0].type, "html_block")
        self.assertTrue("<div>" in tokens[0].content)
        self.assertEqual(tokens[1].type, "html_block")
        self.assertTrue("<!-- comment -->" in tokens[1].content)

    def test_parse_paragraph(self):
        parser = MarkdownParser("This is a simple paragraph.")
        tokens = parser.parse()
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].type, "paragraph")
        self.assertEqual(tokens[0].content, "This is a simple paragraph.")

class TestMarkdownAnalyzer(unittest.TestCase):
    def setUp(self):
        self.test_file_content = """# Title
A paragraph with a [link](http://example.com) and `code`.

* List item
```python
print("Hello")
```
> A quote

| Head1 | Head2 |
|---|---|
| R1C1 | R1C2 |

<!-- HTML Comment -->

[^foot]: A footnote.

This paragraph uses the footnote [^foot].
"""
        self.test_file = create_temp_md_file(content=self.test_file_content)
        self.analyzer = MarkdownAnalyzer(self.test_file)

    def tearDown(self):
        remove_temp_file(self.test_file)

    def test_from_string(self):
        analyzer_str = MarkdownAnalyzer.from_string("# Hello")
        self.assertEqual(len(analyzer_str.tokens), 1)
        self.assertEqual(analyzer_str.tokens[0].type, "header")

    @patch('requests.get')
    def test_from_url_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "# Hello from URL"
        # For from_url, content.decode() is used, so mock .content
        mock_response.content = b"# Hello from URL" 
        mock_get.return_value = mock_response

        analyzer_url = MarkdownAnalyzer.from_url("http://fakeurl.com/test.md")
        self.assertEqual(len(analyzer_url.tokens), 1)
        self.assertEqual(analyzer_url.tokens[0].type, "header")
        self.assertEqual(analyzer_url.tokens[0].content, "Hello from URL")
        mock_get.assert_called_once_with("http://fakeurl.com/test.md", timeout=10)

    @patch('requests.get')
    def test_from_url_failure(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("Failed to connect")
        with self.assertRaises(requests.exceptions.RequestException):
            MarkdownAnalyzer.from_url("http://fakeurl.com/test.md")


    def test_identify_headers(self):
        headers = self.analyzer.identify_headers()
        self.assertIn("Header", headers)
        self.assertEqual(len(headers["Header"]), 1)
        self.assertEqual(headers["Header"][0]["text"], "Title")

    def test_identify_paragraphs(self):
        paragraphs = self.analyzer.identify_paragraphs()
        self.assertIn("Paragraph", paragraphs)
        self.assertEqual(len(paragraphs["Paragraph"]), 2) 
        self.assertTrue("A paragraph with a" in paragraphs["Paragraph"][0])

    def test_identify_blockquotes(self):
        blockquotes = self.analyzer.identify_blockquotes()
        self.assertIn("Blockquote", blockquotes)
        self.assertEqual(len(blockquotes["Blockquote"]), 1)
        self.assertEqual(blockquotes["Blockquote"][0], "A quote")

    def test_identify_code_blocks(self):
        code_blocks = self.analyzer.identify_code_blocks()
        self.assertIn("Code block", code_blocks)
        self.assertEqual(len(code_blocks["Code block"]), 1)
        self.assertEqual(code_blocks["Code block"][0]["language"], "python")

    def test_identify_lists(self):
        lists = self.analyzer.identify_lists()
        self.assertIn("Unordered list", lists)
        self.assertEqual(len(lists["Unordered list"][0]), 1) 
        self.assertEqual(lists["Unordered list"][0][0]["text"], "List item")

    def test_identify_tables(self):
        tables = self.analyzer.identify_tables()
        self.assertIn("Table", tables)
        self.assertEqual(len(tables["Table"]), 1)
        self.assertEqual(tables["Table"][0]["header"], ["Head1", "Head2"])

    def test_identify_links(self):
        links = self.analyzer.identify_links()
        self.assertIn("Text Link", links) # Key name changed
        self.assertEqual(len(links["Text Link"]), 1)
        self.assertEqual(links["Text Link"][0]["url"], "http://example.com")

    def test_identify_footnotes(self):
        footnotes = self.analyzer.identify_footnotes()
        self.assertEqual(len(footnotes), 1)
        self.assertEqual(footnotes[0]["id"], "foot")
        self.assertEqual(footnotes[0]["content"], "A footnote.")

    def test_identify_inline_code(self):
        inline_code = self.analyzer.identify_inline_code()
        self.assertEqual(len(inline_code), 1)
        self.assertEqual(inline_code[0]["code"], "code")

    def test_identify_html_blocks(self):
        html_blocks = self.analyzer.identify_html_blocks()
        self.assertEqual(len(html_blocks), 1)
        self.assertTrue("<!-- HTML Comment -->" in html_blocks[0]["content"])

    def test_get_tokens_sequential(self):
        sequential_elements = self.analyzer.get_tokens_sequential()
        self.assertTrue(len(sequential_elements) > 5) 
        self.assertEqual(sequential_elements[0]['type'], 'header') # Type is 'header', level is in meta
        self.assertEqual(sequential_elements[0]['content'], 'Title')

    def test_analyse(self):
        analysis = self.analyzer.analyse()
        self.assertEqual(analysis['headers'], 1)
        self.assertEqual(analysis['paragraphs'], 2)
        self.assertEqual(analysis['code_blocks'], 1)
        self.assertTrue(analysis['words'] > 10)


class TestMDXMarkdownParser(unittest.TestCase):
    def test_parse_jsx_import(self):
        md_text = "import MyComponent from './MyComponent';"
        parser = MDXMarkdownParser(md_text)
        tokens = parser.parse() 
        # Current MDX parser treats non-code as paragraphs or similar
        # This test might need adjustment based on how MDX specific elements are tokenized
        self.assertTrue(any(t.type == 'paragraph' and md_text in t.content for t in tokens) or not tokens)


    def test_parse_jsx_component_block(self):
        md_text = "<MyComponent>\n  Content\n</MyComponent>"
        parser = MDXMarkdownParser(md_text)
        tokens = parser.parse()
        self.assertTrue(any(t.type == 'paragraph' and md_text in t.content for t in tokens) or not tokens)


    def test_mdx_fenced_code_block_handling(self):
        md_text = "```javascript mdx\n<Button>Click Me</Button>\n```"
        parser = MDXMarkdownParser(md_text)
        tokens = parser.parse()
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].type, "code")
        self.assertEqual(tokens[0].meta["language"], "javascript mdx")
        self.assertEqual(tokens[0].content, "<Button>Click Me</Button>") # No added indent in this version


class TestMDXMarkdownAnalyzer(unittest.TestCase):
    def setUp(self):
        self.mdx_content = """---
title: MDX Test
---
import Button from './Button';

# MDX Document

<Button>Click Me</Button>

```javascript
console.log("hello");
```
"""
        self.test_file = create_temp_md_file(filename="temp_test_file.mdx", content=self.mdx_content)
        self.analyzer = MDXMarkdownAnalyzer.from_file(self.test_file) # Use classmethod

    def tearDown(self):
        remove_temp_file(self.test_file)

    def test_mdx_analyzer_code_blocks(self):
        code_blocks = self.analyzer.identify_code_blocks()
        self.assertIn("Code block", code_blocks)
        self.assertEqual(len(code_blocks["Code block"]), 1)
        self.assertEqual(code_blocks["Code block"][0]["language"], "javascript")
        self.assertEqual(code_blocks["Code block"][0]["content"].strip(), 'console.log("hello");')

    def test_mdx_identify_jsx_imports(self):
        imports = self.analyzer.identify_jsx_imports()
        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0]["source"], "./Button")


class TestWebsiteScraper(unittest.TestCase):
    @patch('requests.get')
    def test_scrape_single_page(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><h1>Hello</h1></body></html>"
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_get.return_value = mock_response

        scraper = WebsiteScraper("http://example.com", max_depth=0)
        pages = scraper.scrape()

        self.assertEqual(len(pages), 1)
        self.assertIn("http://example.com", pages) # Normalized URL might be http://example.com
        self.assertEqual(pages["http://example.com"], mock_response.text)
        mock_get.assert_called_once_with("http://example.com", timeout=10, headers=unittest.mock.ANY)


    @patch('requests.get')
    def test_scrape_with_depth_and_links(self, mock_get):
        responses = {
            "http://example.com": MagicMock(status_code=200, text="<html><a href='/page2'>Page 2</a></html>", headers={'Content-Type': 'text/html'}),
            "http://example.com/page2": MagicMock(status_code=200, text="<html>Page 2 content</html>", headers={'Content-Type': 'text/html'})
        }
        mock_get.side_effect = lambda url, timeout, headers: responses[url]

        scraper = WebsiteScraper("http://example.com", max_depth=1)
        pages = scraper.scrape()

        self.assertEqual(len(pages), 2)
        self.assertIn("http://example.com", pages)
        self.assertIn("http://example.com/page2", pages)
        self.assertEqual(mock_get.call_count, 2)

    def test_is_valid_url(self):
        scraper = WebsiteScraper("http://example.com")
        self.assertTrue(scraper._is_valid_url("http://example.com/path"))
        self.assertFalse(scraper._is_valid_url("http://anotherdomain.com")) 
        self.assertFalse(scraper._is_valid_url("ftp://example.com")) 
        self.assertTrue(scraper._is_valid_url("http://example.com/test.html")) # html is fine
        self.assertFalse(scraper._is_valid_url("http://example.com/test.pdf")) # pdf is not


class TestMarkdownConverter(unittest.TestCase):
    def test_convert_simple_html(self):
        converter = MarkdownConverter()
        html = "<h1>Title</h1><p>Text</p>"
        markdown = converter.convert(html)
        self.assertIn("# Title", markdown) 
        self.assertIn("Text", markdown)

    def test_convert_with_atx_style(self):
        converter = MarkdownConverter(heading_style="ATX")
        html = "<h1>Title</h1>"
        markdown = converter.convert(html)
        self.assertEqual(markdown.strip(), "# Title")

    @patch('markdown_analyzer_lib.markdown_analyzer.md') # Corrected patch path
    def test_convert_heading_style_passed(self, mock_markdownify_md):
        converter = MarkdownConverter(heading_style="SETEXT")
        html_content = "<h1>Hello</h1>"
        converter.convert(html_content)
        mock_markdownify_md.assert_called_once_with(html_content, heading_style="SETEXT")


class TestWebsiteMarkdownDocument(unittest.TestCase):
    @patch('markdown_analyzer_lib.markdown_analyzer.WebsiteScraper.scrape') # Corrected patch path
    @patch('markdown_analyzer_lib.markdown_analyzer.MarkdownConverter.convert') # Corrected patch path
    def test_generate_document(self, mock_convert, mock_scrape):
        mock_scrape.return_value = {
            "http://example.com": "<html><head><title>Home Page</title></head><body><h1>Home</h1></body></html>", # Added title tag
            "http://example.com/about": "<html><head><title>About Us</title></head><body><h1>About</h1></body></html>"
        }
        mock_convert.side_effect = lambda html: "# " + BeautifulSoup(html, "html.parser").h1.text if BeautifulSoup(html, "html.parser").h1 else "Converted"

        doc_generator = WebsiteMarkdownDocument("http://example.com", max_depth=1)
        markdown_doc = doc_generator.generate()
        
        self.assertIn("# Site Index", markdown_doc)
        self.assertIn("- [Home Page](#home-page)  <!-- Original URL: http://example.com -->", markdown_doc) # Anchor uses title
        self.assertIn("- [About Us](#about-us)  <!-- Original URL: http://example.com/about -->", markdown_doc) # Anchor uses title
        self.assertIn("## <a id='home-page'></a>Home Page\n", markdown_doc)
        self.assertIn("<!-- Source URL: http://example.com -->\n# Home", markdown_doc)
        self.assertIn("## <a id='about-us'></a>About Us\n", markdown_doc)
        self.assertIn("<!-- Source URL: http://example.com/about -->\n# About", markdown_doc)


    def test_extract_title_from_markdown(self): # Renamed from _extract_title
        title = WebsiteMarkdownDocument._extract_title_from_markdown("# My Title\nContent")
        self.assertEqual(title, "My Title")
        title_no_h1 = WebsiteMarkdownDocument._extract_title_from_markdown("Just content")
        self.assertEqual(title_no_h1, "Untitled Page")

    def test_url_to_anchor_slug(self): # Renamed from _url_to_anchor
        anchor = WebsiteMarkdownDocument._url_to_anchor_slug("http://example.com/some/page", title="Some Page", for_header=True)
        self.assertEqual(anchor, "some-page")
        anchor_root = WebsiteMarkdownDocument._url_to_anchor_slug("http://example.com/", title="Index", for_header=True)
        self.assertEqual(anchor_root, "index")
        anchor_from_url = WebsiteMarkdownDocument._url_to_anchor_slug("http://example.com/another-path/")
        self.assertEqual(anchor_from_url, "another-path")


class TestMarkdownSiteConverter(unittest.TestCase):
    @patch('markdown_analyzer_lib.markdown_analyzer.WebsiteMarkdownDocument.generate') # Corrected patch path
    def test_convert_site_to_markdown_no_output_file(self, mock_generate):
        mock_generate.return_value = "# Mocked Markdown Document"

        converter = MarkdownSiteConverter("http://example.com")
        result = converter.convert_site_to_markdown()

        self.assertEqual(result, "# Mocked Markdown Document")
        mock_generate.assert_called_once_with(include_index_param=True, page_separator_param="\n\n---\n\n")


    @patch('markdown_analyzer_lib.markdown_analyzer.WebsiteMarkdownDocument.generate') # Corrected patch path
    @patch('builtins.open', new_callable=mock_open)
    def test_convert_site_to_markdown_with_output_file(self, mock_file_open, mock_generate):
        mock_generate.return_value = "# Mocked Document for File"
        output_filename = "test_output.md"

        converter = MarkdownSiteConverter("http://example.com")
        result = converter.convert_site_to_markdown(output_file=output_filename)

        self.assertEqual(result, "# Mocked Document for File")
        mock_generate.assert_called_once_with(include_index_param=True, page_separator_param="\n\n---\n\n")
        mock_file_open.assert_called_once_with(output_filename, "w", encoding="utf-8")
        mock_file_open().write.assert_called_once_with("# Mocked Document for File")


class TestMarkdownDocument(unittest.TestCase):
    def setUp(self):
        self.md_content = "# Test Doc\nPar [link](url)"
        self.test_file = create_temp_md_file(content=self.md_content)

    def tearDown(self):
        remove_temp_file(self.test_file)

    def test_from_file(self):
        doc = MarkdownDocument.from_file(self.test_file)
        self.assertIsInstance(doc.analyzer, MarkdownAnalyzer)
        self.assertEqual(len(doc.get_headers()), 1)

    @patch('markdown_analyzer_lib.markdown_analyzer.MarkdownAnalyzer.from_url') # Corrected patch path
    def test_from_url(self, mock_analyzer_from_url):
        mock_analyzer_instance = MagicMock(spec=MarkdownAnalyzer)
        mock_analyzer_instance.text = "# From URL" # Ensure mock has text attribute
        mock_analyzer_from_url.return_value = mock_analyzer_instance
        
        doc = MarkdownDocument.from_url("http://fake.com/doc.md")
        self.assertEqual(doc.analyzer, mock_analyzer_instance)
        mock_analyzer_from_url.assert_called_once_with("http://fake.com/doc.md", encoding='utf-8')

    @patch('markdown_analyzer_lib.markdown_analyzer.MarkdownAnalyzer.from_string') # Corrected patch path
    def test_from_string(self, mock_analyzer_from_string):
        mock_analyzer_instance = MagicMock(spec=MarkdownAnalyzer)
        mock_analyzer_instance.text = "# Hello String" # Ensure mock has text attribute
        mock_analyzer_from_string.return_value = mock_analyzer_instance

        doc = MarkdownDocument.from_string("# Hello String")
        self.assertEqual(doc.analyzer, mock_analyzer_instance)
        mock_analyzer_from_string.assert_called_once_with("# Hello String", encoding='utf-8')
    
    def test_init_fallback_to_string(self):
        # This test is tricky because the original MarkdownDocument.__init__ was removed.
        # The current __init__ expects one of file_path, source_text, or url.
        # The old fallback logic is no longer directly applicable.
        # We can test that providing a string directly works as intended.
        with patch('markdown_analyzer_lib.markdown_analyzer.logger') as mock_logger: # Corrected patch path
            doc = MarkdownDocument(source_text="NonExistentFile.md #This is a title")
            self.assertIsInstance(doc.analyzer, MarkdownAnalyzer)
            self.assertEqual(len(doc.get_headers()), 1) 
            mock_logger.warning.assert_not_called() # No warning should be called for direct string


    def test_get_summary(self):
        doc = MarkdownDocument.from_file(self.test_file)
        summary = doc.get_summary()
        self.assertEqual(summary['headers'], 1)
        self.assertEqual(summary['paragraphs'], 1)

    def test_get_headers(self):
        doc = MarkdownDocument.from_file(self.test_file)
        headers = doc.get_headers()
        self.assertEqual(len(headers), 1)
        self.assertEqual(headers[0]['text'], "Test Doc")

    def test_get_paragraphs(self):
        doc = MarkdownDocument.from_file(self.test_file)
        paragraphs = doc.get_paragraphs()
        self.assertEqual(len(paragraphs), 1)
        self.assertEqual(paragraphs[0], "Par [link](url)") 

    def test_get_links(self):
        doc = MarkdownDocument.from_file(self.test_file)
        links = doc.get_links()
        self.assertEqual(len(links['Text Link']), 1)
        self.assertEqual(links['Text Link'][0]['text'], "link")

    def test_get_code_blocks(self):
        doc_with_code = MarkdownDocument.from_string("```python\npass\n```")
        code_blocks = doc_with_code.get_code_blocks()
        self.assertEqual(len(code_blocks), 1)
        self.assertEqual(code_blocks[0]['language'], "python")

    def test_get_sequential_elements(self):
        doc = MarkdownDocument.from_file(self.test_file)
        elements = doc.get_sequential_elements()
        self.assertTrue(len(elements) >= 1) 
        self.assertEqual(elements[0]['type'], 'header') # First token is header


if __name__ == '__main__':
    import sys 
    try:
        import requests 
    except ImportError:
        mock_requests_module = type(sys)('requests') 
        class RequestExceptionInMock(Exception): pass
        mock_requests_module.RequestException = RequestExceptionInMock # type: ignore
        mock_exceptions_submodule = type(sys)('requests.exceptions')
        mock_exceptions_submodule.RequestException = RequestExceptionInMock # type: ignore
        mock_requests_module.exceptions = mock_exceptions_submodule # type: ignore
        def mock_get(*args, **kwargs): raise RequestExceptionInMock("requests module not installed, using mock.")
        mock_requests_module.get = mock_get # type: ignore
        sys.modules['requests'] = mock_requests_module 
        globals()['requests'] = mock_requests_module
    
    unittest.main()
