"""
MCP System Information Module

IMPORTANT: When calling functions, pass ONLY the values, not parameter names.
CORRECT: get_system_info()
WRONG: get_system_info(system="windows")
"""

import platform
import os
import sys
import json


def get_system_info() -> dict:
    """
    Get current system basic information.

    Returns:
    - Dictionary containing system information (dict):
      - os_name: Operating system name (string)
      - os_version: Operating system version (string)
      - os_release: Operating system release (string)
      - architecture: System architecture (string)
      - machine: Machine type (string)
      - processor: Processor information (string)
      - python_version: Python version (string)
      - python_compiler: Python compiler information (string)
      - python_implementation: Python implementation (string) (CPython, PyPy, etc.)
      - cwd: Current working directory (string)
      - user: Current username (string)
      - cpu_count: CPU core count (integer)
      - memory_info: Memory information (string, Linux/Mac only)

    Note:
    - This function only uses Python standard library, no third-party packages required

    Example call:
    get_system_info()
    Returns: {"os_name": "Windows", "python_version": "3.9.0", ...}
    """
    system_info = {}

    try:
        # Operating system information
        system_info['os_name'] = platform.system()  # Windows, Linux, Darwin (Mac)
        system_info['os_version'] = platform.version()
        system_info['os_release'] = platform.release()

        # System architecture information
        system_info['architecture'] = platform.architecture()[0]  # 32bit, 64bit
        system_info['machine'] = platform.machine()  # x86_64, AMD64, etc.
        system_info['processor'] = platform.processor() or "Unknown"

        # Python information
        system_info['python_version'] = sys.version
        system_info['python_compiler'] = platform.python_compiler()
        system_info['python_implementation'] = platform.python_implementation()

        # Runtime information
        system_info['cwd'] = os.getcwd()
        system_info['user'] = os.getenv('USERNAME') or os.getenv('USER') or "Unknown"
        system_info['cpu_count'] = os.cpu_count() or 0

        # Platform-specific information
        if platform.system() == "Windows":
            system_info['platform_info'] = platform.platform()
        elif platform.system() == "Linux":
            # Try to get Linux distribution information
            try:
                with open('/etc/os-release', 'r') as f:
                    for line in f:
                        if line.startswith('PRETTY_NAME='):
                            system_info['linux_distro'] = line.split('=')[1].strip().strip('"')
                            break
            except:
                system_info['linux_distro'] = "Unknown"

            # Try to get memory information (Linux only)
            try:
                with open('/proc/meminfo', 'r') as f:
                    mem_lines = f.readlines()[:3]
                    system_info['memory_info'] = [line.strip() for line in mem_lines]
            except:
                system_info['memory_info'] = "Not available"
        elif platform.system() == "Darwin":  # Mac OS
            system_info['mac_version'] = platform.mac_ver()[0]

    except Exception as e:
        # If an error occurs while getting information, record the error but continue returning what was obtained
        system_info['error'] = f"Partial information retrieval failed: {str(e)}"

    return system_info


def format_system_info(system_info: dict, format_type: str = 'text') -> str:
    """
    Format system information output.

    Parameters:
    - system_info: System information dictionary returned by get_system_info (dict, required)
      Example: {"os_name": "Windows", "python_version": "3.9.0", ...}

    - format_type: Output format (string, optional, defaults to 'text')
      Allowed values: 'text', 'json', or 'html'
      Example: "json"

    Returns:
    - Formatted system information string (string)

    Raises:
    - ValueError: Format type not supported

    Example call:
    format_system_info({"os_name": "Windows"}, "json")
    Returns: '{"os_name": "Windows", ...}'
    """
    if format_type == 'text':
        lines = []
        lines.append("=" * 50)
        lines.append("System Information Report")
        lines.append("=" * 50)

        for key, value in system_info.items():
            if isinstance(value, list):
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"{key}: {value}")

        lines.append("=" * 50)
        return "\n".join(lines)

    elif format_type == 'json':
        return json.dumps(system_info, indent=2, ensure_ascii=False)

    elif format_type == 'html':
        html = "<html><head><title>System Information</title></head><body>"
        html += "<h1>System Information Report</h1>"
        html += "<table border='1' cellpadding='5'>"

        for key, value in system_info.items():
            if isinstance(value, list):
                html += f"<tr><td><b>{key}</b></td><td>"
                for item in value:
                    html += f"{item}<br>"
                html += "</td></tr>"
            else:
                html += f"<tr><td><b>{key}</b></td><td>{value}</td></tr>"

        html += "</table></body></html>"
        return html

    else:
        raise ValueError(f"Unsupported format type: {format_type}")
