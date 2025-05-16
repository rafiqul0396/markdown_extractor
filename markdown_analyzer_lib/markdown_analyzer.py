#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete module for parsing, analyzing, and converting Markdown documents,
including the full transformation of a website into a structured Markdown document.

This module also integrates MDX support and some useful extensions.
"""

import re
import logging
import os
import json
from collections import defaultdict, deque
from urllib.parse import urljoin, urlparse, urlunparse
from typing import Optional, Set, Dict, Any, List, Tuple 

import requests
from bs4 import BeautifulSoup, PageElement 
from markdownify import markdownify as md

logger = logging.getLogger(__name__)

# =============================================================================
# PART 1: MARKDOWN / MDX PARSING AND ANALYSIS
# =============================================================================

class BlockToken:
    """Represents a block-level token in Markdown."""
    def __init__(self, type_: str, content: str = "", level: Optional[int] = None, meta: Optional[Dict[str, Any]] = None, line: Optional[int] = None):
        self.type = type_
        self.content = content
        self.level = level
        self.meta = meta or {}
        self.line = line

class InlineParser:
    """Parses inline Markdown elements within a block."""
    IMAGE_OR_LINK_RE = re.compile(r'(!?\[([^\]]*)\])(\(([^\)]+)\)|\[([^\]]+)\])') 
    CODE_INLINE_RE = re.compile(r'`([^`]+)`') 
    EMPHASIS_RE = re.compile(r'(\*\*|__)(.*?)\1|\*(.*?)\*|_(.*?)_') 
    FOOTNOTE_RE = re.compile(r'\[\^([^\]]+)\]') 
    HTML_INLINE_RE = re.compile(r'<[a-zA-Z/][^>]*>') 
    HTML_INLINE_BLOCK_RE = re.compile(r'<([a-zA-Z]+)([^>]*)>(.*?)</\1>', re.DOTALL) 

    def __init__(self, references: Optional[Dict[str, str]] = None, footnotes: Optional[Dict[str, str]] = None):
        self.references: Dict[str, str] = references or {}
        self.footnotes: Dict[str, str] = footnotes or {}

    def parse_inline(self, text: str) -> Dict[str, List[Any]]:
        result: Dict[str, List[Any]] = {
            "text_links": [], "image_links": [], "inline_code": [],
            "emphasis": [], "footnotes_used": [], "html_inline": []
        }
        used_footnotes: Set[str] = set()
        for fm in self.FOOTNOTE_RE.finditer(text):
            fid = fm.group(1)
            if fid in self.footnotes and fid not in used_footnotes:
                used_footnotes.add(fid)
                result["footnotes_used"].append({"id": fid, "content": self.footnotes[fid]})
        for cm in self.CODE_INLINE_RE.finditer(text):
            result["inline_code"].append(cm.group(1))
        for em_match in self.EMPHASIS_RE.finditer(text):
            emphasized_text = em_match.group(2) or em_match.group(3) or em_match.group(4)
            if emphasized_text: result["emphasis"].append(emphasized_text)
        soup = BeautifulSoup(text, 'html.parser')
        for tag_element in soup.find_all(): result["html_inline"].append(str(tag_element))
        
        for mm in self.IMAGE_OR_LINK_RE.finditer(text):
            prefix_and_alt = mm.group(1) 
            alt_or_text = mm.group(2)    
            url_direct = mm.group(4)     
            url_ref_id = mm.group(5)     

            is_image = prefix_and_alt.startswith('!')
            final_url: Optional[str] = None

            if url_direct:
                final_url = url_direct
            elif url_ref_id and url_ref_id.lower() in self.references:
                final_url = self.references[url_ref_id.lower()]
            
            if final_url:
                entry = {"alt_text": alt_or_text, "url": final_url} if is_image else {"text": alt_or_text, "url": final_url}
                result["image_links" if is_image else "text_links"].append(entry)
        return result

class MarkdownParser:
    FRONTMATTER_RE = re.compile(r'^---\s*$')
    ATX_HEADER_RE = re.compile(r'^(#{1,6})\s+(.*)$')
    SETEXT_H1_RE = re.compile(r'^=+\s*$')
    SETEXT_H2_RE = re.compile(r'^-+\s*$')
    FENCE_RE = re.compile(r'^```([^`]*)$')
    BLOCKQUOTE_RE = re.compile(r'^(>\s?)(.*)$')
    ORDERED_LIST_RE = re.compile(r'^\s*\d+\.\s+(.*)$')
    UNORDERED_LIST_RE = re.compile(r'^\s*[-+*]\s+(.*)$')
    HR_RE = re.compile(r'^(\*{3,}|-{3,}|_{3,})\s*$')
    TABLE_SEPARATOR_RE = re.compile(r'^\|?(\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?\s*$')
    REFERENCE_DEF_RE = re.compile(r'^\[([^\]]+)\]:\s+(.*?)\s*$', re.MULTILINE)
    FOOTNOTE_DEF_RE = re.compile(r'^\[\^([^\]]+)\]:\s+(.*?)\s*$', re.MULTILINE)
    HTML_BLOCK_START = re.compile(r'^(<([a-zA-Z]+)([^>]*)>|<!--)')
    HTML_BLOCK_END_COMMENT = re.compile(r'-->\s*$')

    def __init__(self, text: str):
        self.lines: List[str] = text.split('\n')
        self.length: int = len(self.lines)
        self.pos: int = 0
        self.tokens: List[BlockToken] = []
        self.text: str = text
        self.references: Dict[str, str] = {}
        self.footnotes: Dict[str, str] = {}
        self.extract_references_and_footnotes()

    def extract_references_and_footnotes(self) -> None:
        for m in self.REFERENCE_DEF_RE.finditer(self.text): self.references[m.group(1).lower()] = m.group(2)
        for m in self.FOOTNOTE_DEF_RE.finditer(self.text): self.footnotes[m.group(1)] = m.group(2)

    def parse(self) -> List[BlockToken]:
        if self.pos < self.length and self.FRONTMATTER_RE.match(self.lines[self.pos].strip()): self.parse_frontmatter()
        while self.pos < self.length:
            if self.pos >= self.length: break
            line = self.lines[self.pos]
            if not line.strip(): self.pos += 1; continue
            if line.startswith("    ") or line.startswith("\t"): self.parse_indented_code_block(); continue
            if self.is_table_start(): self.parse_table(); continue
            if self.is_html_block_start(line): self.parse_html_block(); continue
            m_atx = self.ATX_HEADER_RE.match(line)
            if m_atx: self.tokens.append(BlockToken('header', content=m_atx.group(2).strip(), level=len(m_atx.group(1)), line=self.pos+1)); self.pos += 1; continue
            if self.pos+1 < self.length:
                next_line_strip = self.lines[self.pos+1].strip()
                if self.SETEXT_H1_RE.match(next_line_strip): self.tokens.append(BlockToken('header', content=line.strip(), level=1, line=self.pos+1)); self.pos += 2; continue
                if self.SETEXT_H2_RE.match(next_line_strip): self.tokens.append(BlockToken('header', content=line.strip(), level=2, line=self.pos+1)); self.pos += 2; continue
            if self.HR_RE.match(line.strip()): self.tokens.append(BlockToken('hr', line=self.pos+1)); self.pos += 1; continue
            fm_fence = self.FENCE_RE.match(line.strip())
            if fm_fence: self.parse_fenced_code_block(fm_fence.group(1).strip()); continue
            bm_bq = self.BLOCKQUOTE_RE.match(line)
            if bm_bq: self.parse_blockquote(); continue
            om_list, um_list = self.ORDERED_LIST_RE.match(line), self.UNORDERED_LIST_RE.match(line)
            if om_list or um_list: self.parse_list(ordered=bool(om_list)); continue
            self.parse_paragraph()
        return self.tokens

    def parse_indented_code_block(self) -> None:
        start = self.pos; code_lines: List[str] = []
        while self.pos < self.length:
            line = self.lines[self.pos]
            if line.startswith("    "): code_lines.append(line[4:]); self.pos += 1
            elif line.startswith("\t"): code_lines.append(line[1:]); self.pos += 1
            else: break
        if code_lines: self.tokens.append(BlockToken('code', content="\n".join(code_lines), meta={"language": None, "code_type": "indented"}, line=start+1))

    def is_html_block_start(self, line: str) -> bool: return self.HTML_BLOCK_START.match(line.strip()) is not None

    def parse_html_block(self) -> None:
        start = self.pos; html_lines: List[str] = []; first_line_strip = self.lines[self.pos].strip(); comment_mode = first_line_strip.startswith('<!--')
        open_tag_match = None; tag_to_balance = None
        if not comment_mode:
            open_tag_match = self.HTML_BLOCK_START.match(first_line_strip)
            if open_tag_match and open_tag_match.group(2) and not first_line_strip.endswith("/>"): tag_to_balance = open_tag_match.group(2)
        depth = 1 if tag_to_balance else 0
        while self.pos < self.length:
            line = self.lines[self.pos]; html_lines.append(line)
            if comment_mode:
                if self.HTML_BLOCK_END_COMMENT.search(line): self.pos += 1; break
            elif tag_to_balance:
                depth += len(re.findall(f"<{tag_to_balance}[^>]*>", line, re.IGNORECASE)) - len(re.findall(f"</{tag_to_balance}>", line, re.IGNORECASE))
                if depth <= 0 and self.pos > start: self.pos += 1; break
            elif self.pos > start and (not self.lines[self.pos].strip() or self.starts_new_block(self.lines[self.pos].strip())): break
            self.pos += 1
            if self.pos >= self.length and (comment_mode or depth > 0): logger.warning(f"HTML block starting line {start+1} seems unclosed."); break
        self.tokens.append(BlockToken('html_block', content="\n".join(html_lines), line=start+1))

    def is_table_start(self) -> bool:
        if self.pos+1 < self.length:
            return '|' in self.lines[self.pos].strip() and '|' in self.lines[self.pos+1].strip() and self.TABLE_SEPARATOR_RE.match(self.lines[self.pos+1].strip()) is not None
        return False

    def parse_table(self) -> None:
        start = self.pos; header_line_content = self.lines[self.pos].strip(); self.pos += 2
        table_rows_content: List[str] = []
        while self.pos < self.length:
            line = self.lines[self.pos].strip()
            if not line or self.starts_new_block(line) or not '|' in line: break
            table_rows_content.append(line); self.pos += 1
        def parse_table_row(row_str: str) -> List[str]:
            parts = [p.strip() for p in row_str.strip().split('|')]
            if parts and not parts[0]: parts.pop(0)
            if parts and not parts[-1]: parts.pop()
            return parts
        self.tokens.append(BlockToken('table', meta={"header": parse_table_row(header_line_content), "rows": [parse_table_row(row) for row in table_rows_content]}, line=start+1))

    def starts_new_block(self, line: str) -> bool:
        return any(regex.match(line) for regex in [self.ATX_HEADER_RE, self.FRONTMATTER_RE, self.FENCE_RE, self.BLOCKQUOTE_RE, self.ORDERED_LIST_RE, self.UNORDERED_LIST_RE, self.HR_RE, self.HTML_BLOCK_START])

    def parse_frontmatter(self) -> None:
        self.pos += 1; start = self.pos; fm_lines: List[str] = []
        while self.pos < self.length:
            if self.FRONTMATTER_RE.match(self.lines[self.pos].strip()): fm_lines = self.lines[start:self.pos]; self.pos += 1; break
            self.pos += 1
        else: fm_lines = self.lines[start:]; self.pos = self.length; logger.warning(f"Frontmatter starting at line {start} seems unclosed.")
        self.tokens.append(BlockToken('frontmatter', content="\n".join(fm_lines), line=start))

    def parse_fenced_code_block(self, lang: str) -> None:
        initial_line_num = self.pos; fence_marker = self.lines[initial_line_num].strip()[:3]; self.pos += 1; start_content_pos = self.pos
        code_lines_content: List[str] = []
        while self.pos < self.length:
            line = self.lines[self.pos]
            if line.strip() == fence_marker:
                code_lines_content = self.lines[start_content_pos:self.pos]; self.pos += 1
                self.tokens.append(BlockToken('code', content="\n".join(code_lines_content), meta={"language": lang, "code_type": "fenced"}, line=initial_line_num+1))
                return
            self.pos += 1
        logger.warning(f"Unclosed code fence starting at line {initial_line_num + 1}. Treating as paragraph."); self.pos = initial_line_num; self.parse_paragraph()

    def parse_blockquote(self) -> None:
        start = self.pos; bq_lines: List[str] = []
        while self.pos < self.length:
            line = self.lines[self.pos]; bm_match = self.BLOCKQUOTE_RE.match(line)
            if bm_match: bq_lines.append(bm_match.group(2)); self.pos += 1
            elif bq_lines and line.strip() and not self.starts_new_block(line.strip()): bq_lines.append(line); self.pos += 1
            else: break
        self.tokens.append(BlockToken('blockquote', content="\n".join(bq_lines), line=start+1))

    def parse_list(self, ordered: bool) -> None:
        start = self.pos; list_items_text: List[str] = []; current_item_lines: List[str] = []
        list_pattern = self.ORDERED_LIST_RE if ordered else self.UNORDERED_LIST_RE
        while self.pos < self.length:
            line = self.lines[self.pos]
            if not line.strip():
                if current_item_lines: list_items_text.append("\n".join(current_item_lines).strip()); current_item_lines = []
                if self.pos + 1 < self.length:
                    next_line_peek = self.lines[self.pos+1]
                    if not list_pattern.match(next_line_peek) and not (next_line_peek.startswith("    ") or next_line_peek.startswith("\t")): self.pos +=1; break 
                else: self.pos +=1; break
                self.pos += 1; continue
            if self.starts_new_block(line.strip()) and not list_pattern.match(line.strip()): break
            lm_match = list_pattern.match(line)
            if lm_match:
                if current_item_lines: list_items_text.append("\n".join(current_item_lines).strip())
                current_item_lines = [lm_match.group(1)]
            elif current_item_lines: current_item_lines.append(line.strip())
            else: break
            self.pos += 1
        if current_item_lines: list_items_text.append("\n".join(current_item_lines).strip())
        task_re = re.compile(r'^\[([ xX])\]\s+(.*)$', re.DOTALL)
        final_items_data: List[Dict[str, Any]] = []
        for item_text_content in list_items_text:
            m_task = task_re.match(item_text_content)
            if m_task: final_items_data.append({"text": m_task.group(2).strip(), "task_item": True, "checked": (m_task.group(1).lower() == 'x')})
            else: final_items_data.append({"text": item_text_content, "task_item": False})
        self.tokens.append(BlockToken('ordered_list' if ordered else 'unordered_list', meta={"items": final_items_data}, line=start+1))

    def parse_paragraph(self) -> None:
        start = self.pos; para_lines: List[str] = []
        while self.pos < self.length:
            line = self.lines[self.pos]
            if not line.strip(): self.pos += 1; break 
            if self.starts_new_block(line.strip()): break
            para_lines.append(line); self.pos += 1
        content = "\n".join(para_lines).strip()
        if content: self.tokens.append(BlockToken('paragraph', content=content, line=start+1))

class MarkdownAnalyzer:
    def __init__(self, file_path: str, encoding: str ='utf-8'):
        try:
            with open(file_path, 'r', encoding=encoding) as f: self.text: str = f.read()
        except Exception as e: logger.error(f"Error reading file {file_path}: {e}"); raise
        parser = MarkdownParser(self.text)
        self.tokens: List[BlockToken] = parser.parse()
        self.references: Dict[str, str] = parser.references
        self.footnotes: Dict[str, str] = parser.footnotes
        self.inline_parser: InlineParser = InlineParser(references=self.references, footnotes=self.footnotes)
        self._parse_inline_tokens()

    @classmethod
    def from_file(cls, file_path: str, encoding: str ='utf-8') -> 'MarkdownAnalyzer':
        return cls(file_path=file_path, encoding=encoding)

    @classmethod
    def from_url(cls, url: str, encoding: str ='utf-8') -> 'MarkdownAnalyzer':
        try:
            response = requests.get(url, timeout=10); response.raise_for_status()
            text = response.content.decode(encoding, errors='replace')
            analyzer = cls.__new__(cls); # type: ignore
            analyzer.text = text 
            parser = MarkdownParser(text)
            analyzer.tokens = parser.parse(); analyzer.references = parser.references
            analyzer.footnotes = parser.footnotes; analyzer.inline_parser = InlineParser(references=analyzer.references, footnotes=analyzer.footnotes)
            analyzer._parse_inline_tokens(); return analyzer
        except requests.RequestException as exc: logger.error(f"Error fetching URL {url}: {exc}"); raise

    @classmethod
    def from_string(cls, markdown_string: str, encoding: str ='utf-8') -> 'MarkdownAnalyzer':
        analyzer = cls.__new__(cls); # type: ignore
        analyzer.text = markdown_string 
        parser = MarkdownParser(markdown_string)
        analyzer.tokens = parser.parse(); analyzer.references = parser.references
        analyzer.footnotes = parser.footnotes; analyzer.inline_parser = InlineParser(references=analyzer.references, footnotes=analyzer.footnotes)
        analyzer._parse_inline_tokens(); return analyzer

    def _parse_inline_tokens(self) -> None:
        for token in self.tokens:
            if token.type in ('paragraph', 'header', 'blockquote') and hasattr(token, 'content') and token.content:
                inline_data = self.inline_parser.parse_inline(token.content)
                if not hasattr(token, 'meta') or token.meta is None: token.meta = {}
                token.meta.update(inline_data)
            elif token.type in ('ordered_list', 'unordered_list') and hasattr(token, 'meta') and token.meta and "items" in token.meta:
                for item in token.meta["items"]:
                    if isinstance(item, dict) and "text" in item and item["text"]: item.update(self.inline_parser.parse_inline(item["text"]))

    def identify_headers(self) -> Dict[str, List[Dict[str, Any]]]: 
        return {"Header": [{"line": t.line, "level": t.level, "text": t.content} for t in self.tokens if t.type == 'header']}
    def identify_paragraphs(self) -> Dict[str, List[str]]: 
        return {"Paragraph": [t.content for t in self.tokens if t.type == 'paragraph']}
    def identify_blockquotes(self) -> Dict[str, List[str]]: 
        return {"Blockquote": [t.content for t in self.tokens if t.type == 'blockquote']}
    def identify_code_blocks(self) -> Dict[str, List[Dict[str, Any]]]: 
        return {"Code block": [{"start_line": t.line, "content": t.content, "language": t.meta.get("language") if t.meta else None, "code_type": t.meta.get("code_type") if t.meta else None} for t in self.tokens if t.type == 'code']}
    def identify_lists(self) -> Dict[str, List[List[Dict[str, Any]]]]: 
        return {"Ordered list": [t.meta["items"] for t in self.tokens if t.type == 'ordered_list' and t.meta and "items" in t.meta], 
                "Unordered list": [t.meta["items"] for t in self.tokens if t.type == 'unordered_list' and t.meta and "items" in t.meta]}
    def identify_tables(self) -> Dict[str, List[Dict[str, Any]]]: 
        return {"Table": [{"header": t.meta["header"], "rows": t.meta["rows"]} for t in self.tokens if t.type == 'table' and t.meta and "header" in t.meta and "rows" in t.meta]}
    
    def identify_links(self) -> Dict[str, List[Dict[str, Any]]]:
        links: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for token in self.tokens:
            if hasattr(token, 'meta') and token.meta:
                for l_type in ["text_links", "image_links"]:
                    link_list = token.meta.get(l_type, [])
                    if link_list: 
                        for link_info in link_list: 
                            links[l_type.replace("_", " ").title()].append({"line": token.line, **link_info})
                if token.type in ('ordered_list', 'unordered_list') and token.meta and "items" in token.meta:
                    for idx, item in enumerate(token.meta["items"]):
                        if isinstance(item, dict):
                            item_line = (token.line or 0) + idx
                            for l_type_item in ["text_links", "image_links"]:
                                item_link_list = item.get(l_type_item, [])
                                if item_link_list: 
                                    for link_info_item in item_link_list: 
                                        links[l_type_item.replace("_", " ").title()].append({"line": item_line, "context": "list_item", **link_info_item})
        return dict(links)

    def identify_footnotes(self) -> List[Dict[str, Any]]:
        footnotes: List[Dict[str, Any]] = []; seen: Set[Tuple[str, str]] = set()
        for token in self.tokens:
            if hasattr(token, 'meta') and token.meta and "footnotes_used" in token.meta:
                for fn in token.meta["footnotes_used"]:
                    key = (str(fn["id"]), str(fn["content"]))
                    if key not in seen: seen.add(key); footnotes.append({"line": token.line, **fn})
        return footnotes

    def identify_inline_code(self) -> List[Dict[str, Any]]: return [{"line": t.line, "code": c} for t in self.tokens if hasattr(t, 'meta') and t.meta for c in t.meta.get("inline_code", [])]
    def identify_emphasis(self) -> List[Dict[str, Any]]: return [{"line": t.line, "text": e} for t in self.tokens if hasattr(t, 'meta') and t.meta for e in t.meta.get("emphasis", [])]
    def identify_task_items(self) -> List[Dict[str, Any]]: return [{"line": (t.line or 0) + i, "text": item["text"], "checked": item["checked"]} for t in self.tokens if t.type in ('ordered_list', 'unordered_list') and hasattr(t, 'meta') and t.meta and "items" in t.meta for i, item in enumerate(t.meta.get("items",[])) if isinstance(item, dict) and item.get("task_item")]
    def identify_html_blocks(self) -> List[Dict[str, Any]]: return [{"line": t.line, "content": t.content} for t in self.tokens if t.type == 'html_block']
    def identify_html_inline(self) -> List[Dict[str, Any]]: return [{"line": t.line, "html": h} for t in self.tokens if hasattr(t, 'meta') and t.meta for h in t.meta.get("html_inline", [])]

    def get_tokens_sequential(self) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []; element_id = 1
        for token in self.tokens:
            token_data: Dict[str, Any] = {'id': element_id, 'type': token.type, 'line': token.line}; element_id +=1
            if token.type == 'header': token_data.update({'level': token.level, 'content': token.content})
            elif token.type in ('paragraph', 'blockquote', 'code', 'html_block', 'frontmatter'): token_data['content'] = token.content
            if token.type == 'code' and token.meta: token_data.update({'language': token.meta.get("language"), 'code_type': token.meta.get("code_type")})
            elif token.type in ('ordered_list', 'unordered_list') and hasattr(token, 'meta') and token.meta and "items" in token.meta:
                token_data['items'] = []
                for item_idx, item_detail in enumerate(token.meta["items"]):
                    item_line = (token.line or 0) + item_idx
                    item_data: Dict[str, Any] = {'id': element_id, 'type': 'task_item' if item_detail.get("task_item") else 'list_item', 'content': item_detail["text"], 'line': item_line}
                    if item_detail.get("task_item"): item_data['checked'] = item_detail.get("checked", False)
                    if isinstance(item_detail, dict): item_data['inline_elements'] = self._extract_inline_for_sequential(item_detail, element_id); element_id += len(item_data.get('inline_elements', []))
                    token_data['items'].append(item_data); element_id +=1
            elif token.type == 'table' and token.meta: token_data.update({'header': token.meta.get("header"), 'rows': token.meta.get("rows")})
            if hasattr(token, 'meta') and token.meta and token.type not in ('ordered_list', 'unordered_list'):
                 token_data['inline_elements'] = self._extract_inline_for_sequential(token.meta, element_id); element_id += len(token_data.get('inline_elements', []))
            result.append(token_data)
        return result

    def _extract_inline_for_sequential(self, meta_dict: Dict[str, Any], start_id: int) -> List[Dict[str, Any]]:
        inline_elements: List[Dict[str, Any]] = []; current_id = start_id
        for key, type_name in [("emphasis", "emphasis"), ("inline_code", "inline_code"), ("text_links", "link"), ("image_links", "image"), ("html_inline", "html_inline"), ("footnotes_used", "footnote_ref")]:
            for item in meta_dict.get(key, []):
                data = {'id': current_id, 'type': type_name}
                if isinstance(item, dict): data.update(item)
                else: data['content' if type_name not in ["link", "image", "footnote_ref"] else ('text' if type_name == "link" else 'alt_text' if type_name == "image" else 'ref_id')] = item
                inline_elements.append(data); current_id += 1
        return inline_elements

    def count_words(self) -> int: return len(self.text.split()) if hasattr(self, 'text') and self.text else 0
    def count_characters(self) -> int: return len([char for char in self.text if not char.isspace()]) if hasattr(self, 'text') and self.text else 0

    def analyse(self) -> Dict[str, Any]:
        analysis: Dict[str, Any] = {
            'headers': len(self.identify_headers().get("Header", [])), 'paragraphs': len(self.identify_paragraphs().get("Paragraph", [])),
            'blockquotes': len(self.identify_blockquotes().get("Blockquote", [])), 'code_blocks': len(self.identify_code_blocks().get("Code block", [])),
            'ordered_list_items': sum(len(g) for g in self.identify_lists().get("Ordered list", []) if g), 
            'unordered_list_items': sum(len(g) for g in self.identify_lists().get("Unordered list", []) if g), 
            'tables': len(self.identify_tables().get("Table", [])), 'html_blocks': len(self.identify_html_blocks()),
            'html_inline_count': len(self.identify_html_inline()), 'words': self.count_words(), 'characters': self.count_characters(),
            'links': len(self.identify_links().get("Text Link", [])) + len(self.identify_links().get("Image Link", [])), 
            'images': len(self.identify_links().get("Image Link", [])), 
            'footnotes': len(self.identify_footnotes()), 'task_items': len(self.identify_task_items()),
        }
        return analysis

class MDXMarkdownParser(MarkdownParser):
    JSX_IMPORT_RE = re.compile(r'^import\s+.*?\s+from\s+["\'](.*?)["\'];?\s*$')
    JSX_COMPONENT_START_RE = re.compile(r'^<([A-Z][A-Za-z0-9]*|[a-z]+\.[A-Z][A-Za-z0-9]*).*?(?:>|\/>)$')
    JSX_COMPONENT_END_RE = re.compile(r'^</([A-Z][A-Za-z0-9]*|[a-z]+\.[A-Z][A-Za-z0-9]*)>$')
    def __init__(self, text: str): super().__init__(text)
    def parse(self) -> List[BlockToken]:
        super().parse(); processed_tokens: List[BlockToken] = []
        for token in self.tokens: 
            if token.type == 'paragraph' and hasattr(token, 'content') and self.JSX_COMPONENT_START_RE.match(token.content.strip().split('\n')[0]): pass
            if hasattr(token, 'content') and self.JSX_IMPORT_RE.match(token.content): pass
            processed_tokens.append(token)
        self.tokens = processed_tokens; return self.tokens

class MDXMarkdownAnalyzer(MarkdownAnalyzer):
    def __init__(self, file_path: Optional[str]=None, markdown_string: Optional[str]=None, from_url: Optional[str]=None, encoding: str='utf-8'):
        text_content: Optional[str] = None
        if file_path: 
            try:
                with open(file_path, 'r', encoding=encoding) as f: text_content = f.read()
            except Exception as e: logger.error(f"Error reading MDX file {file_path}: {e}"); raise
        elif markdown_string is not None: text_content = markdown_string
        elif from_url: 
            try:
                response = requests.get(from_url, timeout=10); response.raise_for_status(); text_content = response.content.decode(encoding, errors='replace')
            except requests.RequestException as exc: logger.error(f"Error fetching MDX from URL {from_url}: {exc}"); raise
        else: raise ValueError("Source required for MDXMarkdownAnalyzer.")
        if text_content is None: raise ValueError("No content for MDXMarkdownAnalyzer.")
        
        self.text: str = text_content
        parser = MDXMarkdownParser(self.text) 
        self.tokens: List[BlockToken] = parser.parse()
        self.references: Dict[str, str] = parser.references
        self.footnotes: Dict[str, str] = parser.footnotes
        self.inline_parser: InlineParser = InlineParser(references=self.references, footnotes=self.footnotes)
        self._parse_inline_tokens()

    @classmethod
    def from_file(cls, file_path: str, encoding: str='utf-8') -> 'MDXMarkdownAnalyzer': return cls(file_path=file_path, encoding=encoding)
    @classmethod
    def from_string(cls, markdown_string: str, encoding: str='utf-8') -> 'MDXMarkdownAnalyzer': return cls(markdown_string=markdown_string, encoding=encoding)
    @classmethod
    def from_url(cls, url: str, encoding: str='utf-8') -> 'MDXMarkdownAnalyzer': return cls(from_url=url, encoding=encoding)
    
    def identify_jsx_imports(self) -> List[Dict[str, Any]]: return [{"line": i+1, "statement": l.strip(), "source": m.group(1)} for i, l in enumerate(self.text.splitlines()) if (m := MDXMarkdownParser.JSX_IMPORT_RE.match(l.strip()))]
    def identify_jsx_components(self) -> List[Dict[str, Any]]: return [{"line": t.line, "content": t.content} for t in self.tokens if t.type == 'html_block' and hasattr(t, 'content') and MDXMarkdownParser.JSX_COMPONENT_START_RE.match(t.content.strip().split('\n')[0])]
    
    def analyse(self) -> Dict[str, Any]: 
        analysis = super().analyse()
        analysis['jsx_imports'] = len(self.identify_jsx_imports())
        # Potentially add more MDX specific counts here
        return analysis

# =============================================================================
# PART 2: CONVERTING A WEBSITE TO A STRUCTURED MARKDOWN DOCUMENT
# =============================================================================

class WebsiteScraper:
    def __init__(self, base_url: str, max_depth: int = 2, timeout: int = 10):
        self.base_url = base_url; self.max_depth = max_depth; self.timeout = timeout
        self.visited: Set[str] = set(); parsed_base_url = urlparse(base_url)
        if not parsed_base_url.scheme or not parsed_base_url.netloc: raise ValueError("Invalid base_url.")
        self.domain: str = parsed_base_url.netloc

    def scrape(self) -> Dict[str, str]:
        pages: Dict[str, str] = {}; queue: deque[Tuple[str, int]] = deque([(self.base_url, 0)]); self.visited.clear()
        while queue:
            current_url, depth = queue.popleft()
            if current_url in self.visited or depth > self.max_depth: continue
            normalized_url = self._normalize_url(current_url)
            if normalized_url in self.visited: continue
            logger.info("Scraping %s (depth %d)", normalized_url, depth)
            try: response = requests.get(normalized_url, timeout=self.timeout, headers={'User-Agent': 'MarkdownAnalyzerLibScraper/1.0'}); response.raise_for_status()
            except requests.RequestException as exc: logger.error(f"Download error {normalized_url}: {exc}"); continue
            if 'text/html' not in response.headers.get('Content-Type', '').lower(): logger.warning(f"Skipping non-HTML {normalized_url}"); self.visited.add(normalized_url); continue
            html_content = response.text; pages[normalized_url] = html_content; self.visited.add(normalized_url)
            soup = BeautifulSoup(html_content, "html.parser")
            for link_tag in soup.find_all("a", href=True):
                if not isinstance(link_tag, PageElement) or not hasattr(link_tag, 'get'): continue
                href_val = link_tag.get("href"); href_str: str = ""
                if href_val: href_str = href_val[0] if isinstance(href_val, list) and href_val else (str(href_val) if not isinstance(href_val, list) else "")
                if href_str:
                    try:
                        next_url_abs = urljoin(normalized_url, href_str.strip())
                        if self._is_valid_url(next_url_abs) and self._normalize_url(next_url_abs) not in self.visited: queue.append((next_url_abs, depth + 1))
                    except Exception as e: logger.warning(f"Link process error '{href_str}' on {normalized_url}: {e}")
        return pages

    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(url); path = parsed.path or '/'; query = '&'.join(sorted(parsed.query.split('&'))) if parsed.query else ''
        return urlunparse((str(parsed.scheme).lower(), str(parsed.netloc).lower(), str(path), str(parsed.params), str(query), '')).rstrip('/')

    def _is_valid_url(self, url: str) -> bool:
        try: parsed = urlparse(url)
        except ValueError: logger.warning(f"Invalid URL skipped: {url}"); return False
        return parsed.scheme in {"http", "https"} and parsed.netloc == self.domain and not (parsed.path and parsed.path.lower().endswith(('.pdf', '.jpg', '.png', '.zip', '.exe', '.mp4', '.mov', '.css', '.js')))

class MarkdownConverter:
    def __init__(self, heading_style: str = "ATX", **options: Any): self.heading_style = heading_style; self.options = options
    def convert(self, html: str) -> str:
        try:
            if 'strip' in self.options and isinstance(self.options['strip'], str): self.options['strip'] = [self.options['strip']]
            return md(html, heading_style=self.heading_style, **self.options)
        except Exception as e: logger.error(f"HTML conversion error: {e}"); return f"<!-- Conversion Error: {e} -->\n{html[:500]}..."

class WebsiteMarkdownDocument:
    def __init__(self, base_url: str, max_depth: int = 2, scraper_timeout: int = 10, converter_options: Optional[Dict[str, Any]] = None):
        self.base_url = base_url; self.max_depth = max_depth
        self.scraper = WebsiteScraper(base_url, max_depth, scraper_timeout)
        self.converter = MarkdownConverter(**(converter_options or {}))
        self.pages: Dict[str, str] = {}

    def generate(self, include_index_param: bool = True, page_separator_param: str = "\n\n---\n\n") -> str: 
        html_pages_data = self.scraper.scrape() 
        if not html_pages_data: logger.warning(f"No pages from {self.base_url}."); return ""
        logger.info("Converting %d pages to Markdown", len(html_pages_data))
        sorted_urls = sorted(html_pages_data.keys())
        for url_key in sorted_urls: self.pages[url_key] = self.converter.convert(html_pages_data[url_key])
        document_lines: List[str] = []
        if include_index_param: 
            document_lines.append("# Site Index\n")
            for url_key_idx in sorted_urls:
                title = self._extract_title_from_html(html_pages_data[url_key_idx]) or self._extract_title_from_markdown(self.pages[url_key_idx])
                anchor = self._url_to_anchor_slug(url_key_idx, title)
                document_lines.append(f"- [{title}]({anchor})  <!-- Original URL: {url_key_idx} -->")
            document_lines.append(page_separator_param) 
        for url_key_content in sorted_urls:
            markdown = self.pages[url_key_content]
            title_content = self._extract_title_from_html(html_pages_data[url_key_content]) or self._extract_title_from_markdown(markdown)
            anchor_slug = self._url_to_anchor_slug(url_key_content, title_content, for_header=True)
            document_lines.extend([f"\n## <a id='{anchor_slug}'></a>{title_content}\n", f"<!-- Source URL: {url_key_content} -->\n", markdown.strip(), page_separator_param]) 
        return "".join(document_lines).strip()

    @staticmethod
    def _extract_title_from_html(html_text: str) -> str:
        if not html_text: return "Untitled Page"
        soup = BeautifulSoup(html_text, "html.parser"); title_tag = soup.title
        if title_tag and hasattr(title_tag, 'string') and title_tag.string: return title_tag.string.strip()
        h1_tag = soup.find("h1")
        if h1_tag and hasattr(h1_tag, 'string') and h1_tag.string: return h1_tag.string.strip()
        return "Untitled Page"
    @staticmethod
    def _extract_title_from_markdown(markdown_text: str) -> str:
        if not markdown_text: return "Untitled Page"
        for line in markdown_text.splitlines():
            if line.strip().startswith("# "): return line.strip().lstrip("# ").strip()
        return "Untitled Page"
    @staticmethod
    def _url_to_anchor_slug(url: str, title: Optional[str] = None, for_header: bool = False) -> str:
        raw_slug_text = title if for_header and title and title != "Untitled Page" else (urlparse(url).path.strip("/") or "index")
        slug = re.sub(r'[^\w\s-]', '', raw_slug_text.lower()); slug = re.sub(r'[-\s]+', '-', slug).strip('-')
        return slug or "section"

class MarkdownSiteConverter:
    def __init__(self, base_url: str, max_depth: int = 2, scraper_timeout: int = 10, converter_options: Optional[Dict[str, Any]] =None):
        self.document_generator = WebsiteMarkdownDocument(base_url, max_depth, scraper_timeout, converter_options)
    def convert_site_to_markdown(self, output_file: Optional[str] = None, include_index: bool =True, page_separator: str ="\n\n---\n\n") -> str:
        markdown_doc = self.document_generator.generate(include_index_param=include_index, page_separator_param=page_separator) 
        if output_file:
            try: 
                with open(output_file, "w", encoding="utf-8") as f: f.write(markdown_doc)
                logger.info(f"Site Markdown to {output_file}")
            except IOError as exc: logger.error(f"File write error {output_file}: {exc}")
        return markdown_doc

# =============================================================================
# PART 3: ABSTRACTION FOR A MARKDOWN DOCUMENT
# =============================================================================

class MarkdownDocument:
    def __init__(self, source_text: Optional[str] = None, file_path: Optional[str] = None, url: Optional[str] = None, is_mdx: bool = False, encoding: str = 'utf-8'):
        analyzer_class: Any = MDXMarkdownAnalyzer if is_mdx else MarkdownAnalyzer; self.analyzer: Any
        if file_path: self.analyzer = analyzer_class.from_file(file_path, encoding=encoding)
        elif source_text is not None: self.analyzer = analyzer_class.from_string(source_text, encoding=encoding)
        elif url: self.analyzer = analyzer_class.from_url(url, encoding=encoding)
        else: raise ValueError("Source required for MarkdownDocument.")
        if not hasattr(self.analyzer, 'text'): 
            # This case should ideally not be hit if from_url/from_string correctly initialize 'text' on the instance they return
            logger.error("Analyzer instance lacks 'text' attribute after creation.")
            raise AttributeError("Analyzer instance created via from_url or from_string did not properly initialize 'text'.")
        self.text: str = self.analyzer.text
        
    @classmethod
    def from_file(cls, file_path: str, is_mdx: bool = False, encoding: str = 'utf-8') -> 'MarkdownDocument': return cls(file_path=file_path, is_mdx=is_mdx, encoding=encoding)
    @classmethod
    def from_string(cls, markdown_string: str, is_mdx: bool = False, encoding: str = 'utf-8') -> 'MarkdownDocument': return cls(source_text=markdown_string, is_mdx=is_mdx, encoding=encoding)
    @classmethod
    def from_url(cls, url: str, is_mdx: bool = False, encoding: str = 'utf-8') -> 'MarkdownDocument': return cls(url=url, is_mdx=is_mdx, encoding=encoding)
    
    def get_summary(self) -> Dict[str, Any]: return self.analyzer.analyse()
    def get_headers(self) -> List[Dict[str, Any]]: return self.analyzer.identify_headers().get("Header", [])
    def get_paragraphs(self) -> List[str]: return self.analyzer.identify_paragraphs().get("Paragraph", [])
    def get_links(self) -> Dict[str, List[Dict[str, Any]]]: return self.analyzer.identify_links()
    def get_code_blocks(self) -> List[Dict[str, Any]]: return self.analyzer.identify_code_blocks().get("Code block", [])
    def get_sequential_elements(self) -> List[Dict[str, Any]]: return self.analyzer.get_tokens_sequential()
    def get_raw_text(self) -> str: return self.text
    def get_tables(self) -> List[Dict[str, Any]]: return self.analyzer.identify_tables().get("Table", [])
    def get_lists(self) -> Dict[str, List[List[Dict[str, Any]]]]: return self.analyzer.identify_lists()
    def get_blockquotes(self) -> List[str]: return self.analyzer.identify_blockquotes().get("Blockquote", [])
    def get_task_items(self) -> List[Dict[str, Any]]: return self.analyzer.identify_task_items()
    def get_jsx_imports(self) -> List[Dict[str, Any]]:
        if isinstance(self.analyzer, MDXMarkdownAnalyzer): return self.analyzer.identify_jsx_imports()
        logger.warning("JSX import identification only for MDX."); return []
