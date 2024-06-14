import os
import requests
from bs4 import BeautifulSoup
from typing import Optional, Type, Any
from pydantic.v1 import BaseModel, Field
from crewai_tools import BaseTool

class FixedScrapeWebsiteToolQuerySchema(BaseModel):
	"""Input for ScrapeWebsiteToolQuery."""
	pass

class ScrapeWebsiteToolQuerySchema(FixedScrapeWebsiteToolQuerySchema):
	"""Input for ScrapeWebsiteToolQuery."""
	website_url: str = Field(..., description="Mandatory website url to read")
	query: str = Field(..., description="Mandatory what query do you want to perform on the website")

class ScrapeWebsiteToolQuery(BaseTool):
	name: str = "Query website html"
	description: str = "A tool that can be used to query a website's html content."
	args_schema: Type[BaseModel] = ScrapeWebsiteToolQuerySchema
	website_url: Optional[str] = None
	query: Optional[str] = None
	cookies: Optional[dict] = None
	headers: Optional[dict] = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
		'Accept-Language': 'en-US,en;q=0.9',
		'Referer': 'https://www.google.com/',
		'Connection': 'keep-alive',
		'Upgrade-Insecure-Requests': '1',
		'Accept-Encoding': 'gzip, deflate, br'
	}

	def __init__(self, website_url: Optional[str] = None, query: Optional[str] = None, cookies: Optional[dict] = None, **kwargs):
		super().__init__(**kwargs)
		if website_url is not None and query is not None:
			self.website_url = website_url
			self.query = query
			self.description = f"A tool that can be used to read {website_url}'s content and query it."
			self.args_schema = FixedScrapeWebsiteToolQuerySchema
			self._generate_description()
			if cookies is not None:
				self.cookies = {cookies["name"]: os.getenv(cookies["value"])}

	def _run(
		self,
		**kwargs: Any,
	) -> Any:
		website_url = kwargs.get('website_url', self.website_url)
		query = kwargs.get('query', self.query)
		page = requests.get(
			website_url,
			timeout=15,
			headers=self.headers,
			cookies=self.cookies if self.cookies else {}
		)
		soup = BeautifulSoup(page.content, "html.parser")
		# Remove all script tags
		for script in soup.find_all("script"):
			script.decompose()

		# Get the modified HTML as a string
		modified_html = str(soup)
		return modified_html

