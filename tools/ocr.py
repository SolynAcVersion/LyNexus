"""
MCP OCR Module - Optical Character Recognition
Adapted from https://github.com/hiroi-sora/Umi-OCR/blob/main/docs/http/api_doc.md#/api/doc

IMPORTANT: When calling functions, pass ONLY the values, not parameter names.
CORRECT: ocr_process_pictures("/home/user/image.png")
WRONG: ocr_process_pictures(file_path="/home/user/image.png")
"""

import base64
import os
import json
import time
import requests
from urllib.request import urlopen


def ocr_process_pdf(file_path: str, download_dir: str) -> str:
    """
    Perform OCR text recognition on a local PDF file, output to the specified directory,
    and return the file path.

    Parameters:
    - file_path: Path to the PDF file to process (string, required)
      Must be a PDF file
      Example: "/home/user/documents/report.pdf" or "C:\\Users\\user\\Documents\\report.pdf"
      Note: If using Windows paths with backslashes, escape them: "C:\\\\Users\\\\user\\\\file.pdf"

    - download_dir: Local directory path to save the output (string, required)
      This is only the directory path, not including the filename
      Example: "/home/user/downloads" or "C:\\Users\\user\\Downloads"
      Note: Directory will be created if it does not exist

    Returns:
    - The absolute path where the successfully downloaded file is saved, including filename and extension (string)

    Raises:
    - Exception: When server connection fails or Umi-OCR is not running
    - FileNotFoundError: When the source PDF file does not exist
    - AssertionError: When the OCR task fails or returns an error code

    Example call:
    ocr_process_pdf("/home/user/documents/report.pdf", "/home/user/ocr_output")
    Returns: "/home/user/ocr_output/report.txt"

    Prerequisites:
    - Umi-OCR must be running on http://127.0.0.1:1224
    - Run the executable: .\\tools\\addition\\Umi-OCR\\Umi-OCR.exe
    """

    base_url = "http://127.0.0.1:1224"
    try:
        resp = urlopen(base_url)
        code = resp.getcode()
        if code != 200:
            raise Exception(f"No Umi-OCR running or port not correct! Run .\\tools\\addition\\Umi-OCR\\Umi-OCR.exe")
    except Exception as e:
        raise Exception(f'Failed to access local Umi-OCR: {str(e)}')

    url = "{}/api/doc/upload".format(base_url)

    if not file_path.endswith(".pdf"):
        file_path += '.pdf'

    # Task parameters
    options_json = json.dumps(
        {
            "doc.extractionMode": "mixed",
        }
    )
    with open(file_path, "rb") as file:
        response = requests.post(url, files={"file": file}, data={"json": options_json})
    response.raise_for_status()
    res_data = json.loads(response.text)
    if res_data["code"] == 101:
        # If code == 101, indicates that the server did not receive the uploaded file
        # On some Linux systems, if file_name contains non-ASCII characters, this error might occur
        # In this case, specify a temp_name containing only ASCII characters to construct the upload request

        file_name = os.path.basename(file_path)
        file_prefix, file_suffix = os.path.splitext(file_name)
        temp_name = "temp" + file_suffix
        with open(file_path, "rb") as file:
            response = requests.post(
                url,
                # use temp_name to construct the upload request
                files={"file": (temp_name, file)},
                data={"json": options_json},
            )
        response.raise_for_status()
        res_data = json.loads(response.text)
    assert res_data["code"] == 100, "Task submission failed: {}".format(res_data)

    id = res_data["data"]

    url = "{}/api/doc/result".format(base_url)

    headers = {"Content-Type": "application/json"}
    data_str = json.dumps(
        {
            "id": id,
            "is_data": True,
            "format": "dict",
            "is_unread": True,
        }
    )
    while True:
        time.sleep(1)
        response = requests.post(url, data=data_str, headers=headers)
        response.raise_for_status()
        res_data = json.loads(response.text)
        assert res_data["code"] == 100, "Failed to get task status: {}".format(res_data)

        if res_data["is_done"]:
            state = res_data["state"]
            assert state == "success", "Task execution failed: {}".format(
                res_data["message"]
            )
            break

    url = "{}/api/doc/download".format(base_url)

    download_options = {
        "file_types": [
            "txt",
        ],
        "ignore_blank": False,  # Do not ignore blank pages
    }
    download_options["id"] = id
    data_str = json.dumps(download_options)
    response = requests.post(url, data=data_str, headers=headers)
    response.raise_for_status()
    res_data = json.loads(response.text)
    assert res_data["code"] == 100, "Failed to get download URL: {}".format(res_data)

    url = res_data["data"]
    name = res_data["name"]

    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    download_path = os.path.join(download_dir, name)
    response = requests.get(url, stream=True)
    response.raise_for_status()
    # Download file size
    downloaded_size = 0
    log_size = 10485760  # Print progress every 10MB

    with open(download_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)
                downloaded_size += len(chunk)
                if downloaded_size >= log_size:
                    log_size = downloaded_size + 10485760

    url = "{}/api/doc/clear/{}".format(base_url, id)

    response = requests.get(url)
    response.raise_for_status()
    res_data = json.loads(response.text)
    assert res_data["code"] == 100, "Task cleanup failed: {}".format(res_data)
    return download_path


def ocr_process_pictures(file_path: str) -> list:
    """
    Perform OCR text recognition on a local image file and return the recognized content.

    Parameters:
    - file_path: Path to the image file to process (string, required)
      Example: "/home/user/pictures/screenshot.png" or "C:\\Users\\user\\Pictures\\scan.jpg"
      Note: If using Windows paths with backslashes, escape them: "C:\\\\Users\\\\user\\\\image.png"
      Supported formats: PNG, JPG, JPEG, BMP, etc.

    Returns:
    - A list of OCR result dictionaries (list)
      Each dictionary contains:
      - text (str): Recognized text content
      - score (float): Confidence score (0~1)
      - box (list): XY coordinates of four corners of the text box in clockwise order: [top-left, top-right, bottom-right, bottom-left]
      - end (str): End character for this line of text based on layout analysis. May be empty, space " ", or newline "\\n"

      To reconstruct complete paragraphs from OCR text blocks, concatenate in the format:
      current_line_text + current_line_end + next_line_text + next_line_end + ...

    Raises:
    - FileNotFoundError: When the image file does not exist
    - Exception: When Umi-OCR server connection fails or returns an error
    - ValueError: When the image format is not supported

    Example call:
    ocr_process_pictures("/home/user/images/receipt.png")
    Returns: [
        {
            "text": "Total: $25.99",
            "score": 0.98,
            "box": [[100, 200], [300, 200], [300, 220], [100, 220]],
            "end": "\\n"
        },
        {
            "text": "Thank you for shopping",
            "score": 0.95,
            "box": [[100, 230], [350, 230], [350, 250], [100, 250]],
            "end": ""
        }
    ]

    Prerequisites:
    - Umi-OCR must be running on http://127.0.0.1:1224
    - Run the executable: .\\tools\\addition\\Umi-OCR\\Umi-OCR.exe
    """

    with open(file_path,'rb') as f:
        image_base64 = base64.b64encode(f.read())
        _, image_base64, _ = str(image_base64).split('\'')
    url = "http://127.0.0.1:1224/api/ocr"
    data = {
        "base64": str(image_base64),
        "options": {
            "data.format": "dict",
        }
    }
    headers = {"Content-Type": "application/json"}
    data_str = json.dumps(data)
    response = requests.post(url, data=data_str, headers=headers)
    response.raise_for_status()
    res_dict = json.loads(response.text)
    return res_dict["data"]
