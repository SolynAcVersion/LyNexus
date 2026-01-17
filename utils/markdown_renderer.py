"""
Markdown and LaTeX Renderer for Chat Interface
Supports incremental rendering for streaming output
Author: Lynexus AI Assistant
Version: 1.0.0
"""

import re
import html
from typing import Optional, Tuple
from enum import Enum

try:
    import markdown
    from markdown.extensions import fenced_code, tables, nl2br
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    print("[MarkdownRenderer] Warning: markdown library not available")

try:
    from markdown_katex import KatexExtension
    KATEX_AVAILABLE = True
except ImportError:
    KATEX_AVAILABLE = False
    print("[MarkdownRenderer] Warning: markdown-katex not available, LaTeX support disabled")


class RenderMode(Enum):
    """Rendering mode"""
    PLAIN_TEXT = "plain"
    STREAMING = "streaming"  # Incremental rendering during stream
    FINAL = "final"  # Complete rendering


class MarkdownRenderer:
    """
    Markdown and LaTeX renderer with streaming support
    """

    # Patterns for detection
    LATEX_BLOCK_PATTERN = re.compile(r'\$\$([^$]+)\$\$', re.MULTILINE)
    LATEX_INLINE_PATTERN = re.compile(r'\$([^$]+)\$')
    CODE_BLOCK_PATTERN = re.compile(r'```(\w*)\n([\s\S]*?)```', re.MULTILINE)
    INLINE_CODE_PATTERN = re.compile(r'`([^`]+)`')
    BOLD_PATTERN = re.compile(r'\*\*([^*]+)\*\*')
    ITALIC_PATTERN = re.compile(r'\*([^*]+)\*')
    HEADER_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    LIST_PATTERN = re.compile(r'^(\s*)[-*+]\s+(.+)$', re.MULTILINE)

    def __init__(self):
        self.md = self._init_markdown()

    def _init_markdown(self):
        """Initialize markdown processor"""
        if not MARKDOWN_AVAILABLE:
            return None

        extensions = [
            'fenced_code',
            'tables',
            'sane_lists',
            'codehilite',
            'nl2br',  # 自动将换行符转换为 <br>
        ]

        # Add KaTeX if available
        if KATEX_AVAILABLE:
            extensions.append(KatexExtension())

        try:
            md = markdown.Markdown(extensions=extensions)
            return md
        except Exception as e:
            print(f"[MarkdownRenderer] Error initializing markdown: {e}")
            return None

    def render(self, text: str, mode: RenderMode = RenderMode.FINAL) -> str:
        """
        Render markdown text to HTML

        Args:
            text: Markdown text to render
            mode: Rendering mode (plain, streaming, or final)

        Returns:
            Rendered HTML string
        """
        if mode == RenderMode.PLAIN_TEXT:
            return self._escape_text(text)

        if not MARKDOWN_AVAILABLE or self.md is None:
            return self._escape_text(text)

        try:
            # Reset markdown instance
            self.md.reset()

            # Convert markdown to HTML
            html_content = self.md.convert(text)

            # Apply custom styling and cleanup
            html_content = self._apply_styling(html_content, mode)

            return html_content
        except Exception as e:
            print(f"[MarkdownRenderer] Error rendering markdown: {e}")
            return self._escape_text(text)

    def render_incremental(self, accumulated_text: str, new_chunk: str) -> Tuple[str, bool]:
        """
        Incremental rendering for streaming output

        Strategy:
        1. If new_chunk doesn't end with newline, return plain text (still streaming line)
        2. If ends with newline, render the complete text up to this point

        Args:
            accumulated_text: Previously accumulated text
            new_chunk: New chunk of text to add

        Returns:
            Tuple of (rendered_html, should_render)
        """
        combined = accumulated_text + new_chunk

        # Check if we should render (line complete)
        # Render on newlines or common Markdown block endings
        should_render = (
            new_chunk.endswith('\n') or
            new_chunk.endswith('```') or
            bool(self.LATEX_BLOCK_PATTERN.search(new_chunk))
        )

        if should_render:
            return self.render(combined, mode=RenderMode.STREAMING), True
        else:
            # Still streaming, return escaped text
            return self._escape_text(combined), False

    def finalize_rendering(self, text: str) -> str:
        """
        Final complete rendering after streaming finishes

        Args:
            text: Complete text to render

        Returns:
            Fully rendered HTML
        """
        return self.render(text, mode=RenderMode.FINAL)

    def _escape_text(self, text: str) -> str:
        """Escape text as HTML (for plain text display)"""
        return html.escape(text).replace('\n', '<br>')

    def _apply_styling(self, html_content: str, mode: RenderMode) -> str:
        """
        Apply custom CSS styling to HTML

        Args:
            html_content: Raw HTML from markdown
            mode: Rendering mode

        Returns:
            Styled HTML
        """
        # Wrap in div with styling
        styled = f'<div class="markdown-content">{html_content}</div>'

        # Additional CSS classes for different modes
        if mode == RenderMode.STREAMING:
            styled = styled.replace('class="markdown-content"',
                                    'class="markdown-content streaming"')

        return styled

    @staticmethod
    def get_base_css() -> str:
        """
        Get base CSS for markdown rendering
        Include this in your application's stylesheet
        """
        return """
        /* Markdown Content Base Styles */
        .markdown-content {
            font-family: 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif;
            font-size: 14px;
            line-height: 1.8;
            color: #e0e0e0;
        }

        /* Headers */
        .markdown-content h1, .markdown-content h2,
        .markdown-content h3, .markdown-content h4,
        .markdown-content h5, .markdown-content h6 {
            margin-top: 1.2em;
            margin-bottom: 0.8em;
            font-weight: 600;
            color: #ffffff;
            line-height: 1.3;
        }

        .markdown-content h1 { font-size: 1.8em; border-bottom: 1px solid #444; padding-bottom: 0.3em; }
        .markdown-content h2 { font-size: 1.5em; border-bottom: 1px solid #444; padding-bottom: 0.3em; }
        .markdown-content h3 { font-size: 1.3em; }
        .markdown-content h4 { font-size: 1.1em; }
        .markdown-content h5 { font-size: 1em; }
        .markdown-content h6 { font-size: 0.9em; color: #aaa; }

        /* Paragraphs */
        .markdown-content p {
            margin: 1em 0;
            line-height: 1.8;
        }

        /* Code blocks */
        .markdown-content pre {
            background-color: #1e1e1e;
            border: 1px solid #333;
            border-radius: 6px;
            padding: 12px;
            overflow-x: auto;
            margin: 1em 0;
            line-height: 1.5;
        }

        .markdown-content code {
            background-color: #2a2a2a;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
        }

        .markdown-content pre code {
            background-color: transparent;
            padding: 0;
            border-radius: 0;
        }

        /* Inline code */
        .markdown-content p code {
            background-color: #2a2a2a;
            color: #e0e0e0;
        }

        /* Blockquotes */
        .markdown-content blockquote {
            border-left: 4px solid #4a9eff;
            margin: 1em 0;
            padding-left: 1em;
            color: #b0b0b0;
            font-style: italic;
        }

        /* Lists */
        .markdown-content ul, .markdown-content ol {
            margin: 1em 0;
            padding-left: 2em;
        }

        .markdown-content li {
            margin: 0.8em 0;
            line-height: 1.8;
            display: list-item;
        }

        .markdown-content ol li {
            margin-bottom: 1em;
        }

        .markdown-content ul li {
            margin-bottom: 0.8em;
        }

        /* Tables */
        .markdown-content table {
            border-collapse: collapse;
            margin: 1em 0;
            width: 100%;
        }

        .markdown-content th, .markdown-content td {
            border: 1px solid #444;
            padding: 8px 12px;
            text-align: left;
        }

        .markdown-content th {
            background-color: #2a2a2a;
            font-weight: 600;
        }

        .markdown-content tr:nth-child(even) {
            background-color: #252525;
        }

        /* Links */
        .markdown-content a {
            color: #4a9eff;
            text-decoration: none;
        }

        .markdown-content a:hover {
            text-decoration: underline;
        }

        /* Horizontal rules */
        .markdown-content hr {
            border: none;
            border-top: 1px solid #444;
            margin: 2em 0;
        }

        /* LaTeX/KaTeX */
        .markdown-content .katex {
            font-size: 1.1em;
        }

        .markdown-content .katex-display {
            margin: 1em 0;
            overflow-x: auto;
            overflow-y: hidden;
        }

        /* Streaming mode indicator */
        .markdown-content.streaming {
            opacity: 0.95;
        }

        /* Images */
        .markdown-content img {
            max-width: 100%;
            height: auto;
            border-radius: 6px;
            margin: 1em 0;
        }

        /* Task lists */
        .markdown-content input[type="checkbox"] {
            margin-right: 0.5em;
        }
        """

    @staticmethod
    def has_markdown_syntax(text: str) -> bool:
        """
        Check if text contains markdown syntax

        Args:
            text: Text to check

        Returns:
            True if markdown syntax detected
        """
        patterns = [
            MarkdownRenderer.HEADER_PATTERN,
            MarkdownRenderer.CODE_BLOCK_PATTERN,
            MarkdownRenderer.LATEX_BLOCK_PATTERN,
            MarkdownRenderer.LATEX_INLINE_PATTERN,
            MarkdownRenderer.BOLD_PATTERN,
        ]

        for pattern in patterns:
            if pattern.search(text):
                return True

        return False


# Singleton instance
_renderer_instance = None


def get_renderer() -> MarkdownRenderer:
    """Get singleton renderer instance"""
    global _renderer_instance
    if _renderer_instance is None:
        _renderer_instance = MarkdownRenderer()
    return _renderer_instance
