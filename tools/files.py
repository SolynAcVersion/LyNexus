"""
MCP File Operations Module
Provides basic file operation functionality.

IMPORTANT: When calling functions, pass ONLY the values, not parameter names.
CORRECT: ls("/home/user/documents")
WRONG: ls(directory="/home/user/documents")

Note: All escape characters (like \\n, \\t) in string parameters will be interpreted
according to Python string rules, where \\n represents a newline character.
"""

import os
import shutil
from typing import Union, List, Dict


def mv(source: str, destination: str) -> str:
    """
    Move a file or directory to the specified path.

    Parameters:
    - source: Source file or directory path (string, required)
      Example: "/home/user/documents/file.txt" or "C:\\Users\\user\\Documents\\file.txt"

    - destination: Target path (string, required)
      Example: "/home/user/backup/file.txt" or "C:\\Users\\user\\Backup\\file.txt"

    Returns:
    - Operation result message (string)

    Raises:
    - FileNotFoundError: When the source path does not exist
    - shutil.Error: Errors during the move operation

    Example call:
    mv("/home/user/file.txt", "/home/user/backup/file.txt")
    Returns: "Moved /home/user/file.txt to /home/user/backup/file.txt"
    """
    if not os.path.exists(source):
        raise FileNotFoundError(f"Source not found: {source}")

    shutil.move(source, destination)
    return f"Moved {source} to {destination}"


def cp(source: str, destination: str) -> str:
    """
    Copy a file or directory to the specified path.

    Parameters:
    - source: Source file or directory path (string, required)
      Example: "/home/user/documents/report.pdf" or "C:\\Users\\user\\Documents\\report.pdf"

    - destination: Target path (string, required)
      Example: "/home/user/backup/report.pdf" or "C:\\Users\\user\\Backup\\report.pdf"

    Returns:
    - Operation result message (string)

    Raises:
    - FileNotFoundError: When the source path does not exist
    - shutil.Error: Errors during the copy operation

    Example call:
    cp("/home/user/report.pdf", "/home/user/backup/report.pdf")
    Returns: "Copied /home/user/report.pdf to /home/user/backup/report.pdf"
    """
    if not os.path.exists(source):
        raise FileNotFoundError(f"Source not found: {source}")

    if os.path.isdir(source):
        shutil.copytree(source, destination)
    else:
        shutil.copy2(source, destination)

    return f"Copied {source} to {destination}"


def ls(directory: str = ".") -> str:
    """
    List all files and subdirectories in the specified directory.

    Parameters:
    - directory: The directory path to list (string, optional, defaults to ".")
      Example values: "/home/user/documents" or "C:\\Users\\user\\Documents" or "."

    Returns:
    - String listing the directory contents

    Raises:
    - FileNotFoundError: When the specified directory does not exist

    Example call:
    ls("/home/user/documents")
    Returns: "Contents of /home/user/documents: file1.txt, file2.pdf, folder1"
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")

    items = os.listdir(directory)
    return f"Contents of {directory}: {', '.join(items)}"


def mkdir(directory: str) -> str:
    """
    Create a directory. If the directory already exists, it will not be overwritten.

    Parameters:
    - directory: Path of the directory to create (string, required)
      Example: "/home/user/new_folder" or "C:\\Users\\user\\NewFolder"

    Returns:
    - Operation result message (string)

    Raises:
    - OSError: When directory creation fails

    Example call:
    mkdir("/home/user/new_folder")
    Returns: "Created directory: /home/user/new_folder"
    """
    if os.path.exists(directory):
        return f"Directory already exists: {directory}"

    os.makedirs(directory)
    return f"Created directory: {directory}"


def rm(path: str) -> str:
    """
    Delete a file or directory. If it's a directory, the entire directory tree will be recursively deleted.

    Parameters:
    - path: Path of the file or directory to delete (string, required)
      Example: "/home/user/old_file.txt" or "C:\\Users\\user\\OldFolder"

    Returns:
    - Operation result message (string)

    Raises:
    - FileNotFoundError: When the path does not exist
    - OSError: When deletion fails

    Example call:
    rm("/home/user/old_file.txt")
    Returns: "Deleted: /home/user/old_file.txt"
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Path not found: {path}")

    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)

    return f"Deleted: {path}"


def cat(filepath: str) -> str:
    """
    Read file content and return it.

    Parameters:
    - filepath: Path of the file to read (string, required)
      Example: "/home/user/documents/note.txt" or "C:\\Users\\user\\Documents\\note.txt"

    Returns:
    - File content as a string

    Raises:
    - FileNotFoundError: When the file does not exist
    - UnicodeDecodeError: When the file encoding is not UTF-8 and cannot be decoded with GBK
    - IOError: When file reading fails

    Example call:
    cat("/home/user/documents/note.txt")
    Returns: "This is the content of the file..."
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    # Try UTF-8 encoding first
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        # Try GBK encoding
        try:
            with open(filepath, "r", encoding="gbk") as f:
                content = f.read()
        except UnicodeDecodeError as e:
            raise UnicodeDecodeError(f"Cannot decode file with UTF-8 or GBK: {filepath}") from e

    return content


def write_to_file(text: str, filepath: Union[str, None], mode: str) -> str:
    """
    Write text to a file. If filepath is None, return the text directly.

    Parameters:
    - text: Text to write (string, required)
      Note: Escape characters (like \\n, \\t) will be interpreted according to Python rules.
      If you want to write a literal backslash and n, use \\\\n.
      Example: "Hello, World!\\nThis is a new line." or "Hello\\tWorld"

    - filepath: File path (string or None, required)
      If None, the text will be returned without writing to a file.
      Example: "/home/user/output.txt" or "C:\\Users\\user\\output.txt" or None

    - mode: Write mode (string, required)
      Use "0" for overwrite mode, "1" for append mode.
      Example: "0" or "1"

    Returns:
    - Success message string, or the text itself if filepath is None

    Raises:
    - ValueError: When filepath is an empty string or mode is not '0' or '1'
    - TypeError: When text is not a string type
    - OSError: When file writing fails

    Example call:
    write_to_file("Hello, World!\\n", "/home/user/output.txt", "0")
    Returns: "Wrote text to /home/user/output.txt (overwrite mode)"
    """
    if filepath is None:
        return text

    if not isinstance(text, str):
        raise TypeError("Text must be a string")

    if not filepath.strip():
        raise ValueError("File path cannot be empty")

    if mode not in ('0', '1'):
        raise ValueError("Mode must be '0' (overwrite) or '1' (append)")

    # Ensure directory exists
    save_dir = os.path.dirname(filepath)
    if save_dir and not os.path.exists(save_dir):
        os.makedirs(save_dir, exist_ok=True)

    try:
        if mode == '0':
            # Overwrite mode
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
                if not text.endswith("\n"):
                    f.write("\n")
            return f"Wrote text to {filepath} (overwrite mode)"
        else:  # mode == '1'
            # Append mode
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(text)
                if not text.endswith("\n"):
                    f.write("\n")
            return f"Wrote text to {filepath} (append mode)"
    except Exception as e:
        raise OSError(f"File write failed: {str(e)}")


def find_lines_in_file(
    file_path: str, search_string: str, case_sensitive: bool = True
) -> List[Dict[str, Union[int, str]]]:
    """
    Find all lines containing the specified string in a file.

    Parameters:
    - file_path: Path of the file to search (string, required)
      Example: "/home/user/documents/log.txt" or "C:\\Users\\user\\Documents\\log.txt"

    - search_string: String to search for (string, required, cannot be empty)
      Example: "error" or "WARNING" or "function_name"

    - case_sensitive: Whether to distinguish case (boolean, optional, defaults to True)
      Example: True (case-sensitive) or False (case-insensitive)

    Returns:
    - List of matching lines, each element is a dictionary containing:
      - line_number (int): Line number (starting from 1)
      - content (str): Line content with trailing newline removed
      - original_content (str): Original line content (preserves newline character)

    Raises:
    - ValueError: When the file path is empty or the search string is empty
    - FileNotFoundError: When the file does not exist
    - ValueError: When the path is not a file
    - UnicodeDecodeError: When the file cannot be decoded with UTF-8 or GBK
    - IOError: When file reading fails

    Example call:
    find_lines_in_file("/home/user/log.txt", "error", False)
    Returns: [
        {"line_number": 5, "content": "Error: Connection failed", "original_content": "Error: Connection failed\\n"},
        {"line_number": 12, "content": "Critical error in module", "original_content": "Critical error in module\\n"}
    ]
    """
    if not file_path or not file_path.strip():
        raise ValueError("File path cannot be empty")

    if not search_string or not search_string.strip():
        raise ValueError("Search string cannot be empty")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if not os.path.isfile(file_path):
        raise ValueError(f"Path is not a file: {file_path}")

    matched_lines = []

    def process_file(file_handle):
        for line_number, line in enumerate(file_handle, start=1):
            # Search based on case_sensitive parameter
            if case_sensitive:
                if search_string in line:
                    matched_lines.append(
                        {
                            "line_number": line_number,
                            "content": line.rstrip("\n"),
                            "original_content": line,
                        }
                    )
            else:
                if search_string.lower() in line.lower():
                    matched_lines.append(
                        {
                            "line_number": line_number,
                            "content": line.rstrip("\n"),
                            "original_content": line,
                        }
                    )

    try:
        # Try UTF-8 encoding first
        with open(file_path, "r", encoding="utf-8") as file:
            process_file(file)
    except UnicodeDecodeError:
        # Try GBK encoding
        try:
            with open(file_path, "r", encoding="gbk") as file:
                process_file(file)
        except UnicodeDecodeError as e:
            raise UnicodeDecodeError(f"Cannot decode file with UTF-8 or GBK: {file_path}") from e
    except Exception as e:
        raise IOError(f"File read failed: {str(e)}")

    return matched_lines
