"""
MCP Network Operations Module

IMPORTANT: When calling functions, pass ONLY the values, not parameter names.
CORRECT: download_document("https://example.com/file.pdf", "/home/user/downloads/file.pdf")
WRONG: download_document(url="https://example.com/file.pdf", save_path="/home/user/downloads/file.pdf")
"""

import urllib.request
import os
import urllib.parse
import socket
import re
from typing import Optional


def download_document(url: str, save_path: str) -> str:
    """
    Download a document from the specified URL to local storage.

    Parameters:
    - url: The URL to download from (string, required)
      Must start with http:// or https://
      Example: "https://example.com/document.pdf"

    - save_path: Local save path including filename and extension (string, required)
      Example: "/home/user/downloads/file.pdf" or "C:\\Users\\user\\Downloads\\file.pdf"
      Note: If path contains backslashes, escape them: "C:\\\\Users\\\\user\\\\file.pdf"

    Returns:
    - File save path on successful download (string)

    Raises:
    - ValueError: URL format error or invalid save path
    - Exception: Download failed or file save failed

    Example call:
    download_document("https://example.com/file.pdf", "/home/user/downloads/file.pdf")
    Returns: "/home/user/downloads/file.pdf"
    """
    # Parameter validation
    if not url.startswith(('http://', 'https://')):
        raise ValueError('URL must start with http:// or https://')

    if not save_path or not save_path.strip():
        raise ValueError('Save path cannot be empty')

    # Ensure save directory exists
    save_dir = os.path.dirname(save_path)
    if save_dir and not os.path.exists(save_dir):
        os.makedirs(save_dir, exist_ok=True)

    try:
        # Download file
        urllib.request.urlretrieve(url, save_path)

        # Verify file was downloaded successfully
        if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
            return save_path
        else:
            raise Exception('Downloaded file size is 0 or file does not exist')

    except Exception as e:
        raise Exception(f'Download failed: {str(e)}')


def save_webpage_with_cookie(url: str, save_path: str, cookie: str) -> str:
    """
    Access a webpage with specified cookie and save the webpage source code.

    Parameters:
    - url: The webpage URL to access (string, required)
      Must start with http:// or https://
      Example: "https://example.com/page"

    - save_path: Local save path including filename (string, required)
      Use .html extension for webpages
      Example: "/home/user/webpage.html" or "C:\\Users\\user\\page.html"

    - cookie: Cookie string (string, required)
      Format: "name=value; name2=value2"
      Example: "session_id=abc123; user_token=xyz789"

    Returns:
    - Saved file path (string)

    Raises:
    - ValueError: Invalid parameters
    - Exception: Access failed or save failed

    Example call:
    save_webpage_with_cookie("https://example.com", "/home/user/page.html", "session=abc")
    Returns: "/home/user/page.html"
    """
    # Parameter validation
    if not url.startswith(('http://', 'https://')):
        raise ValueError('URL must start with http:// or https://')

    if not save_path or not save_path.strip():
        raise ValueError('Save path cannot be empty')

    if not cookie or not cookie.strip():
        raise ValueError('Cookie cannot be empty')

    # Ensure save directory exists
    save_dir = os.path.dirname(save_path)
    if save_dir and not os.path.exists(save_dir):
        os.makedirs(save_dir, exist_ok=True)

    try:
        # Create request object
        request = urllib.request.Request(url)

        # Add cookie to request header
        request.add_header('Cookie', cookie)

        # Add User-Agent to simulate browser access
        request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        # Send request and get response
        response = urllib.request.urlopen(request)

        # Read webpage source code (binary data)
        webpage_content = response.read()

        # Save webpage source code to file (binary write)
        with open(save_path, 'wb') as file:
            file.write(webpage_content)

        # Verify file was saved successfully
        if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
            return save_path
        else:
            raise Exception('Saved file size is 0 or file does not exist')

    except Exception as e:
        raise Exception(f'Webpage access failed: {str(e)}')


def extract_links(html_content: str, base_url: str) -> list:
    """
    Extract all external links from HTML content.

    Parameters:
    - html_content: HTML content string (string, required)
      Example: "<html><a href='https://example.com'>Link</a></html>"

    - base_url: Base URL for resolving relative links (string, required)
      Example: "https://example.com/page"

    Returns:
    - List of all extracted external links (list)

    Example call:
    extract_links("<a href='link1'>...</a>", "https://example.com")
    Returns: ["https://example.com/link1"]
    """
    links = []

    # Use regex to extract all links (href attribute in a tags)
    link_patterns = [
        r'href=["\']([^"\']+)["\']',  # Match href="..." or href='...'
        r'href=([^\s>]+)'  # Match href=... (without quotes)
    ]

    for pattern in link_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for match in matches:
            # Clean link (remove possible spaces and special characters)
            link = match.strip()

            # Skip empty links, anchor links, and JavaScript links
            if (not link or
                link.startswith('#') or
                link.lower().startswith('javascript:') or
                link.lower().startswith('mailto:')):
                continue

            # Handle relative links (convert to absolute links)
            if not link.startswith(('http://', 'https://', '//')):
                try:
                    # Use urllib to parse and join links
                    link = urllib.parse.urljoin(base_url, link)
                except:
                    # If parsing fails, skip this link
                    continue

            # Add to list (deduplicated)
            if link not in links:
                links.append(link)

    # Return sorted link list
    return sorted(links)


def validate_url(url: str) -> bool:
    """
    Validate if URL format is correct.

    Parameters:
    - url: The URL to validate (string, required)
      Example: "https://example.com"

    Returns:
    - True if URL is valid, False otherwise (boolean)

    Example call:
    validate_url("https://example.com")
    Returns: True
    """
    if not url or not isinstance(url, str):
        return False

    # Check if starts with http or https
    if not url.startswith(('http://', 'https://')):
        return False

    # Try to parse URL
    try:
        parsed = urllib.parse.urlparse(url)
        # Ensure there's a network location (netloc)
        if not parsed.netloc:
            return False
        # Ensure there's a scheme
        if not parsed.scheme:
            return False
        return True
    except:
        return False


def read_page(url: str, timeout: Optional[float] = None) -> str:
    """
    Read all text from the specified URL and return all text and external links from the webpage.
    Adds timeout limit to avoid long waits.

    Parameters:
    - url: The URL to read from (string, required)
      Must start with http:// or https://
      Example: "https://example.com"

    - timeout: Timeout in seconds (float or None, optional, defaults to system default)
      Example: 10.0 or None

    Returns:
    - All text and external links from the webpage (string)

    Raises:
    - ValueError: URL format error or unable to access
    - TimeoutError: Request timeout
    - Exception: Webpage read failed

    Example call:
    read_page("https://example.com", 10.0)
    Returns: Webpage text content and links
    """
    # Use stricter URL validation
    if not validate_url(url):
        raise ValueError(f'Invalid URL format: {url}')

    try:
        # Create request object, add User-Agent to simulate browser
        request = urllib.request.Request(url)
        request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        request.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
        request.add_header('Accept-Language', 'zh-CN,zh;q=0.9,en;q=0.8')

        # Set global socket timeout
        if timeout:
            socket.setdefaulttimeout(timeout)

        # Send request and get response
        try:
            response = urllib.request.urlopen(request, timeout=timeout)
        except Exception as e:
            # Try more detailed error message
            raise ConnectionError(f'Cannot connect to {url}: {str(e)}')

        # Check response status code
        if response.getcode() != 200:
            raise ConnectionError(f'Server returned status code: {response.getcode()}')

        # Read webpage content (try multiple encodings)
        html_bytes = response.read()

        # Try multiple encodings
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
        html_content = None

        for encoding in encodings:
            try:
                html_content = html_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if html_content is None:
            # If all encodings fail, use 'latin-1' (won't fail, but may be garbled)
            html_content = html_bytes.decode('latin-1', errors='ignore')

        # Extract all text (remove HTML tags)
        # First remove script and style tags and their content
        cleaned_html = re.sub(r'<script.*?>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        cleaned_html = re.sub(r'<style.*?>.*?</style>', '', cleaned_html, flags=re.DOTALL | re.IGNORECASE)

        # Remove all HTML tags
        text_only = re.sub(r'<[^>]+>', ' ', cleaned_html)

        # Remove excess whitespace (multiple spaces, newlines, etc.)
        text_only = re.sub(r'\s+', ' ', text_only)
        text_only = text_only.strip()

        # Extract all external links
        links = extract_links(html_content, url)

        # Format output
        result = []
        result.append("=" * 50)
        result.append(f"Webpage Content (URL: {url})")
        result.append(f"Timeout setting: {timeout if timeout else 'default'} seconds")
        result.append("=" * 50)
        result.append("Webpage text content")
        result.append("-" * 30)
        result.append(text_only[:5000])  # Limit text length to avoid too long

        if len(text_only) > 5000:
            result.append(f"\n... (text too long, truncated, actual length: {len(text_only)} characters)")

        result.append("\n" + "-" * 30)
        result.append("External links list")
        result.append("-" * 30)

        if links:
            for i, link in enumerate(links[:15], 1):  # Limit to first 15 links
                result.append(f"{i}. {link}")
            if len(links) > 15:
                result.append(f"... (total {len(links)} links, showing first 15)")
        else:
            result.append("No external links found")

        result.append("=" * 50)

        return "\n".join(result)

    except socket.timeout:
        raise TimeoutError(f'Request timeout: Did not complete within {timeout} seconds')
    except urllib.error.URLError as e:  # pyright: ignore[reportAttributeAccessIssue]
        if isinstance(e.reason, socket.timeout):
            raise TimeoutError(f'Request timeout: Did not complete within {timeout} seconds')
        else:
            raise ConnectionError(f'Cannot access URL: {str(e)}')
    except Exception as e:
        raise Exception(f'Webpage read failed: {str(e)}')


def search_baidu(query: str, max_results: int = 5, timeout: float = 10.0) -> str:
    """
    Use Baidu to search for keywords and return search result page content.
    Adds timeout limit.

    Parameters:
    - query: Search keyword (string, required)
      Example: "Python tutorial"

    - max_results: Number of results per page (integer, optional, defaults to 5)
      Example: 10

    - timeout: Timeout in seconds (float, optional, defaults to 10.0)
      Example: 15.0

    Returns:
    - Baidu search result page content (string)

    Raises:
    - ValueError: Query keyword is empty or invalid
    - Exception: Search failed

    Example call:
    search_baidu("Python", 5, 10.0)
    Returns: Baidu search results
    """
    # Parameter validation
    if not query or not query.strip():
        raise ValueError('Search keyword cannot be empty')

    if timeout <= 0:
        timeout = 10.0  # Default 10 seconds

    try:
        # URL encode the query
        encoded_query = urllib.parse.quote(query)

        # Build Baidu search URL
        search_url = f"https://www.baidu.com/s?ie=UTF-8&wd={encoded_query}&rn={max_results}"

        # Call read_page function with timeout parameter
        search_results = read_page(search_url, timeout)

        # Add search info to return content
        result_text = f"Baidu search keyword: {query}\n"
        result_text += f"Search URL: {search_url}\n"
        result_text += f"Timeout setting: {timeout} seconds\n"
        result_text += search_results

        return result_text

    except TimeoutError:
        raise TimeoutError(f'Baidu search timeout: Did not complete within {timeout} seconds')
    except Exception as e:
        raise Exception(f'Baidu search failed: {str(e)}')


def test_connection():
    """Test network connection"""
    print("=== Testing Network Connection ===")

    test_urls = [
        ("Baidu", "https://www.baidu.com"),
        ("Example site", "https://example.com"),
        ("Python official site", "https://www.python.org"),
    ]

    for name, url in test_urls:
        try:
            print(f"Testing connection: {name} ({url})")
            result = read_page(url, timeout=5)
            print(f"  ✓ Connection successful")
            print(f"  Text preview: {result[:100]}...\n")
        except TimeoutError as e:
            print(f"  ✗ Connection timeout: {e}\n")
        except ConnectionError as e:
            print(f"  ✗ Connection error: {e}\n")
        except Exception as e:
            print(f"  ✗ Error: {e}\n")
