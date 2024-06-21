from db.database import Database
from db.models import UrlCache

from typing import Dict, Optional, List
from langchain.pydantic_v1 import BaseModel, Field
from crewai_tools import tool
from langchain.tools import BaseTool, StructuredTool, tool
from langchain.agents import Tool

import hashlib, os, requests
from datetime import datetime
from playwright.sync_api import sync_playwright

db = Database()

class ScreenshotQuery(BaseModel):
    url: str = Field(..., description="URL of the website to capture a screenshot")

def uploadFile(file: str, maxDays=1, maxDownloads=None):
    print('Uploading... ', file)
    just_filename = os.path.basename(file)
    print('Just the filename...: ' + just_filename)
    url = "https://transfer.sh/" + just_filename
    headers = {
        'Max-Days': str(maxDays)
    }
    if maxDownloads is not None:
        headers['Max-Downloads'] = str(maxDownloads)
    print('Uploading now')
    with open(file, 'rb') as f:
        data = f.read()
    try:
        response = requests.put(url, headers=headers, data=data)
        print('Uploading .. response', response)
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def generate_hashed_filename(url, extension="jpg"):
    # Use current timestamp and the URL to generate a unique hash
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    hash_object = hashlib.sha256((url + timestamp).encode())
    hex_dig = hash_object.hexdigest()
    return f"{hex_dig}.{extension}"

def take_screenshot(url: str) -> str:
    # Placeholder function to take a screenshot of the website
    filename = generate_hashed_filename(url)
    output_file = os.path.join("/app", filename) # TODO change this to a subdir
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.screenshot(path=output_file, full_page=True, type="jpeg")
        browser.close()
    return output_file

@tool("take_website_screenshot", args_schema=ScreenshotQuery)
def take_website_screenshot_(url: str) -> str:
    """Take a screenshot of a website and upload it to a public server"""
    picture = take_screenshot(url)
    print("captured picture",picture)
    remote_url = uploadFile(picture)
    return remote_url

the_tool = Tool(
    name = "Intermediate Screenshot Tool",
    func=take_website_screenshot_.run,
    description="Take a screenshot of a website and upload it to a public server",
)