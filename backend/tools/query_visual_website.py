from db.database import Database
from db.models import UrlCache

from typing import Dict, Optional, List
from langchain.pydantic_v1 import BaseModel, Field
from crewai_tools import tool
from langchain.tools import BaseTool, StructuredTool, tool
from langchain.agents import Tool

import hashlib, os, requests, base64
from datetime import datetime
from playwright.sync_api import sync_playwright

db = Database()

class ScreenshotQuery(BaseModel):
    url: str = Field(..., description="URL of the website to capture a screenshot")
    query: str = Field(..., description="Natural language query to perform to the screenshot of the website")

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

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

@tool("query_website_screenshot", args_schema=ScreenshotQuery)
def query_website_screenshot_(url: str, query: str) -> str:
    """Query a visual screenshot of a given website"""
    picture = take_screenshot(url) # return file
    image_base64 = encode_image(picture)
    # if we have an OPENAI_API_KEY use gpt-4o, otherwise if we have REPLICATE_API_TOKEN use llava
    # if we have neither, TODO: use the Ollama model with local moondream v2
    if os.getenv('OPENAI_API_KEY'):
        print(f"[query_visual_website][DEBUG]: Using OpenAI for Vision (gpt-4o)")
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                        "type": "text",
                        "text": query
                        },
                        {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                        }
                    ]
                }
            ],
            "max_tokens": 1000,
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers={
           "Content-Type": "application/json",
           "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
        }, json=payload)
        return response.json()

    elif os.getenv('REPLICATE_API_TOKEN'):
       print(f"[query_visual_website][DEBUG]: Using Replicate for Vision (llava)")
       return "Tool not available."
       pass
    else:
       print("QUERY VISUAL WEBSITE: No API key found; Ollama not yet implemented")
       return "Tool not available."

    print("captured picture",picture)
    remote_url = uploadFile(picture)
    return remote_url

the_tool = Tool(
    name = "Query a visual screenshot of a given website",
    func=query_website_screenshot_.run,
    description = "url=to query, query=to ask",
)