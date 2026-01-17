"""
Test script for Markdown and LaTeX rendering
"""

from utils.markdown_renderer import MarkdownRenderer, RenderMode, get_renderer

def test_basic_markdown():
    """Test basic markdown rendering"""
    renderer = get_renderer()

    test_cases = [
        # Basic markdown
        ("# Heading 1\n\nThis is a paragraph with **bold** and *italic* text.", "Basic formatting"),

        # Code blocks
        ("```python\ndef hello():\n    print('Hello, World!')\n```", "Code block"),

        # Lists
        ("- Item 1\n- Item 2\n- Item 3", "Unordered list"),

        # Tables
        ("| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1   | Cell 2   |", "Table"),

        # LaTeX (if available)
        ("Inline math: $E = mc^2$", "Inline LaTeX"),
        ("Block math:\n$$\n\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}\n$$", "Block LaTeX"),
    ]

    print("=" * 60)
    print("Testing Markdown Rendering")
    print("=" * 60)

    for markdown_text, description in test_cases:
        print(f"\n{description}:")
        print(f"Input:\n{markdown_text}")
        print(f"\nOutput:")
        html = renderer.render(markdown_text, mode=RenderMode.FINAL)
        print(html[:200] + "..." if len(html) > 200 else html)
        print("-" * 60)

def test_incremental_rendering():
    """Test incremental rendering for streaming"""
    renderer = get_renderer()

    print("\n" + "=" * 60)
    print("Testing Incremental Rendering (Streaming Simulation)")
    print("=" * 60)

    # Simulate streaming chunks
    chunks = [
        "# Hello World\n",
        "This is a **test** of streaming.\n",
        "Let's see if it works:\n",
        "- Item 1\n",
        "- Item 2\n",
    ]

    accumulated = ""
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}: {repr(chunk)}")

        # Render incrementally
        html, should_render = renderer.render_incremental(accumulated, chunk)
        accumulated += chunk

        print(f"Should render: {should_render}")
        if should_render:
            print(f"Rendered HTML: {html[:100]}...")

    print("\n" + "-" * 60)
    print("Final rendering:")
    final_html = renderer.finalize_rendering(accumulated)
    print(final_html[:300] + "..." if len(final_html) > 300 else final_html)

def test_markdown_detection():
    """Test markdown syntax detection"""
    renderer = MarkdownRenderer()

    print("\n" + "=" * 60)
    print("Testing Markdown Detection")
    print("=" * 60)

    test_cases = [
        "Plain text without formatting",
        "# Heading",
        "**Bold text**",
        "```python\ncode\n```",
        "$E = mc^2$",
    ]

    for text in test_cases:
        has_md = MarkdownRenderer.has_markdown_syntax(text)
        print(f"\nText: {text}")
        print(f"Has markdown: {has_md}")

if __name__ == "__main__":
    try:
        test_basic_markdown()
        test_incremental_rendering()
        test_markdown_detection()
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
