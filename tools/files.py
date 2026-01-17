"""
MCP File Operations Module
Provides basic file operation functionality with detailed parameter descriptions, return value descriptions, and exception handling.
Note: All escape characters (like \\n, \\t) in string parameters will be interpreted according to Python string rules, where \\n represents a newline character.
"""

import os
import shutil
from typing import Union, List, Dict


def mv(source: str, destination: str) -> str:
    """
    Move a file or directory to the specified path.

    Args:
        source (str, REQUIRED): Source file or directory path.
            Example: "/home/user/documents/file.txt" or "C:\\Users\\user\\Documents\\file.txt"
        destination (str, REQUIRED): Target path. If the target path does not exist, use mkdir to create it first.
            Example: "/home/user/backup/file.txt" or "C:\\Users\\user\\Backup\\file.txt"

    Returns:
        str: Operation result message string.

    Raises:
        FileNotFoundError: When the source path does not exist.
        shutil.Error: Errors during the move operation.

    Example:
        mv("/home/user/file.txt", "/home/user/backup/file.txt")
        Returns: "已将 /home/user/file.txt 移动到 /home/user/backup/file.txt"
    """
    if not os.path.exists(source):
        raise FileNotFoundError(f"源文件/目录不存在: {source}")

    shutil.move(source, destination)
    return f"已将 {source} 移动到 {destination}"


def cp(source: str, destination: str) -> str:
    """
    Copy a file or directory to the specified path.

    Args:
        source (str, REQUIRED): Source file or directory path.
            Example: "/home/user/documents/report.pdf" or "C:\\Users\\user\\Documents\\report.pdf"
        destination (str, REQUIRED): Target path.
            Example: "/home/user/backup/report.pdf" or "C:\\Users\\user\\Backup\\report.pdf"

    Returns:
        str: Operation result message string.

    Raises:
        FileNotFoundError: When the source path does not exist.
        shutil.Error: Errors during the copy operation.

    Example:
        cp("/home/user/report.pdf", "/home/user/backup/report.pdf")
        Returns: "已将 /home/user/report.pdf 复制到 /home/user/backup/report.pdf"
    """
    if not os.path.exists(source):
        raise FileNotFoundError(f"源文件/目录不存在: {source}")

    if os.path.isdir(source):
        shutil.copytree(source, destination)
    else:
        shutil.copy2(source, destination)

    return f"已将 {source} 复制到 {destination}"


def ls(directory: str = ".") -> str:
    """
    List all files and subdirectories in the specified directory.

    Args:
        directory (str, OPTIONAL): Directory path to list contents from. Defaults to current directory.
            Example: "/home/user/documents" or "C:\\Users\\user\\Documents" or "." for current directory

    Returns:
        str: String representation of the directory contents list.

    Raises:
        FileNotFoundError: When the specified directory does not exist.

    Example:
        ls("/home/user/documents")
        Returns: "/home/user/documents 中的内容: file1.txt, file2.pdf, folder1"
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"目录不存在: {directory}")

    items = os.listdir(directory)
    return f"{directory} 中的内容: {', '.join(items)}"


def mkdir(directory: str) -> str:
    """
    Create a directory. If the directory already exists, it will not be overwritten.

    Args:
        directory (str, REQUIRED): Path of the directory to create.
            Example: "/home/user/new_folder" or "C:\\Users\\user\\NewFolder"

    Returns:
        str: Operation result message string.

    Raises:
        OSError: When directory creation fails.

    Example:
        mkdir("/home/user/new_folder")
        Returns: "已创建目录: /home/user/new_folder"
    """
    if os.path.exists(directory):
        return f"目录已存在: {directory}"

    os.makedirs(directory)
    return f"已创建目录: {directory}"


def rm(path: str) -> str:
    """
    Delete a file or directory. If it's a directory, the entire directory tree will be recursively deleted.

    Args:
        path (str, REQUIRED): Path of the file or directory to delete.
            Example: "/home/user/old_file.txt" or "C:\\Users\\user\\OldFolder"

    Returns:
        str: Operation result message string.

    Raises:
        FileNotFoundError: When the path does not exist.
        OSError: When deletion fails.

    Example:
        rm("/home/user/old_file.txt")
        Returns: "已删除: /home/user/old_file.txt"
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"文件/目录不存在: {path}")

    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)

    return f"已删除: {path}"


def cat(filepath: str) -> str:
    """
    Read file content and return it.

    Args:
        filepath (str, REQUIRED): Path of the file to read.
            Example: "/home/user/documents/note.txt" or "C:\\Users\\user\\Documents\\note.txt"

    Returns:
        str: File content as a string.

    Raises:
        FileNotFoundError: When the file does not exist.
        UnicodeDecodeError: When the file encoding is not UTF-8 and cannot be decoded with GBK.
        IOError: When file reading fails.

    Example:
        cat("/home/user/documents/note.txt")
        Returns: "This is the content of the file..."
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"文件不存在: {filepath}")

    # 优先使用 UTF-8 编码读取
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        # 尝试使用 GBK 编码
        try:
            with open(filepath, "r", encoding="gbk") as f:
                content = f.read()
        except UnicodeDecodeError as e:
            raise UnicodeDecodeError(f"无法用UTF-8或GBK解码文件: {filepath}") from e


    return content


def write_to_file(text: str, filepath: Union[str, None], mode: str) -> str:
    """
    Write text to a file. If filepath is None, return the text directly.

    Args:
        text (str, REQUIRED): Text to write. Note: Escape characters in the string (like \\n, \\t) will be
            interpreted according to Python rules, where \\n is interpreted as a newline character.
            If you want to write a literal backslash and n, use \\\\n.
            Example: "Hello, World!\\nThis is a new line." or "Hello\\tWorld"
        filepath (Union[str, None], REQUIRED): File path. If None, return text directly.
            Example: "/home/user/output.txt" or "C:\\Users\\user\\output.txt" or None
        mode (str, REQUIRED): Write mode. Use '0' for overwrite, '1' for append.
            Example: "0" (overwrite) or "1" (append)

    Returns:
        str: Success message string, or the text itself if filepath is None.

    Raises:
        ValueError: When filepath is an empty string or mode is not '0' or '1'.
        TypeError: When text is not a string type.
        OSError: When file writing fails.

    Example:
        write_to_file("Hello, World!\\n", "/home/user/output.txt", "0")
        Returns: "已将文本覆盖写入 /home/user/output.txt"
    """
    if filepath is None:
        return text

    if not isinstance(text, str):
        raise TypeError("文本必须是字符串类型")

    if not filepath.strip():
        raise ValueError("文件路径不能为空")

    if mode not in ('0', '1'):
        raise ValueError("mode 必须为 0（覆盖）或 1（追加）")

    # 确保目录存在
    save_dir = os.path.dirname(filepath)
    if save_dir and not os.path.exists(save_dir):
        os.makedirs(save_dir, exist_ok=True)

    try:
        if mode == '0':
            # 覆盖写入
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
                # 如果文本不以换行符结尾，则添加一个
                if not text.endswith("\n"):
                    f.write("\n")
            return f"已将文本覆盖写入 {filepath}"
        else:  # mode == 1
            # 追加写入
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(text)
                if not text.endswith("\n"):
                    f.write("\n")
            return f"已将文本追加写入 {filepath}"
    except Exception as e:
        raise OSError(f"文件写入失败: {str(e)}")


def find_lines_in_file(
    file_path: str, search_string: str, case_sensitive: bool = True
) -> List[Dict[str, Union[int, str]]]:
    """
    Find all lines containing the specified string in a file, and return line numbers, content, and original content.

    Args:
        file_path (str, REQUIRED): Path of the file to search.
            Example: "/home/user/documents/log.txt" or "C:\\Users\\user\\Documents\\log.txt"
        search_string (str, REQUIRED): String to search for, cannot be empty.
            Example: "error" or "WARNING" or "function_name"
        case_sensitive (bool, OPTIONAL): Whether to distinguish case. Defaults to True (case-sensitive).
            Example: True (case-sensitive) or False (case-insensitive)

    Returns:
        List[Dict[str, Union[int, str]]]: List of matching lines, each element is a dictionary containing:
            - line_number (int): Line number (starting from 1)
            - content (str): Line content with trailing newline removed
            - original_content (str): Original line content (preserves newline character)

    Raises:
        ValueError: When the file path is empty or the search string is empty.
        FileNotFoundError: When the file does not exist.
        ValueError: When the path is not a file.
        UnicodeDecodeError: When the file cannot be decoded with UTF-8 or GBK.
        IOError: When file reading fails.

    Example:
        find_lines_in_file("/home/user/log.txt", "error", False)
        Returns: [
            {"line_number": 5, "content": "Error: Connection failed", "original_content": "Error: Connection failed\\n"},
            {"line_number": 12, "content": "Critical error in module", "original_content": "Critical error in module\\n"}
        ]
    """
    if not file_path or not file_path.strip():
        raise ValueError("文件路径不能为空")

    if not search_string or not search_string.strip():
        raise ValueError("搜索字符串不能为空")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    if not os.path.isfile(file_path):
        raise ValueError(f"路径不是文件: {file_path}")

    matched_lines = []

    def process_file(file_handle):
        for line_number, line in enumerate(file_handle, start=1):
            # 根据 case_sensitive 参数决定搜索方式
            if case_sensitive:
                if search_string in line:
                    matched_lines.append(
                        {
                            "line_number": line_number,
                            "content": line.rstrip("\n"),  # 移除行尾换行符
                            "original_content": line,  # 保留原始内容
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
        # 优先使用 UTF-8 编码读取
        with open(file_path, "r", encoding="utf-8") as file:
            process_file(file)
    except UnicodeDecodeError:
        # 尝试使用 GBK 编码
        try:
            with open(file_path, "r", encoding="gbk") as file:
                process_file(file)
        except UnicodeDecodeError as e:
            raise UnicodeDecodeError(f"无法用UTF-8或GBK解码文件: {file_path}") from e
    except Exception as e:
        raise IOError(f"文件读取失败: {str(e)}")

    return matched_lines