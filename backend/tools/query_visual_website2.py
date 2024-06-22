#from db.database import Database
#from db.models import UrlCache

from typing import Dict, Optional, List, Type, Any
from langchain.pydantic_v1 import BaseModel, Field
from crewai_tools import tool
from crewai_tools import BaseTool

import hashlib, os, requests, base64, tempfile
from datetime import datetime
from playwright.sync_api import sync_playwright 

#db = Database()
 
class ScreenshotQuery(BaseModel):
    url: str = Field(..., description="URL of the website to query")
    query: str = Field(..., description="Detailed question to perform about the URL")

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
    temp_dir = tempfile.mkdtemp()
    temp_subdir = os.path.join(temp_dir, "screenshots")
    os.makedirs(temp_subdir, exist_ok=True)

    filename = generate_hashed_filename(url)
    output_file = os.path.join(temp_subdir, filename) # TODO change this to a subdir
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},  # Smaller viewport size
        )
        page = context.new_page()
        page.goto(url) 
        page.screenshot(path=output_file, full_page=True, type="jpeg")
        browser.close()
    return output_file

class QueryVisualWebsite(BaseTool):
    name: str = "Query website visually" 
    description: str = "A tool that can be used to perform visual queries of a given website."
    args_schema: Type[BaseModel] = ScreenshotQuery
    url: Optional[str] = None
    query: Optional[str] = None

    def __call__(self, url: str, query: str, **kwargs):
        super().__init__(**kwargs)
        if url is not None and query is not None:
            self.url = url
            self.query = query
            self.description = f"A tool that can be used to perform visual queries of {self.url}, using vision."
            self.args_schema = ScreenshotQuery
            self._generate_description()
    
    def _run(
        self,
        url: str,
        query: str,
        **kwargs: Any,
    ) -> Any:
        if not url.startswith("http"):
            url = f"https://{url}"
        try:
            picture = take_screenshot(url) # return file
            image_base64 = encode_image(picture)
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
                result = response.json() 
                print("DEBUG, response from Vision", result)
                return result

            elif os.getenv('REPLICATE_API_TOKEN'):
                print(f"[query_visual_website][DEBUG]: Using Replicate for Vision (llava)")
                return "Tool not available."
                pass
            else:
                print("QUERY VISUAL WEBSITE: No API key found; Ollama not yet implemented")
                return "Tool not available."
        except Exception as e:
            print(f"Error querying visual website: {str(e)}")
            return f"Error querying visual website: {str(e)}"