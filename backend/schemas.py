from typing import Dict, Optional, List, Any
from pydantic import BaseModel, Field

class AvatarDetails(BaseModel):
    bgColor: Optional[str] = Field(None, description="Background color of the avatar")
    hairColor: Optional[str] = Field(None, description="Hair color of the avatar")
    shirtColor: Optional[str] = Field(None, description="Shirt color of the avatar")
    skinColor: Optional[str] = Field(None, description="Skin color of the avatar")
    earSize: Optional[str] = Field(None, description="Ear size style of the avatar")
    hairStyle: Optional[str] = Field(None, description="Hair style of the avatar")
    noseStyle: Optional[str] = Field(None, description="Nose style of the avatar")
    shirtStyle: Optional[str] = Field(None, description="Shirt style of the avatar")
    facialHairStyle: Optional[str] = Field(None, description="Facial hair style of the avatar")
    glassesStyle: Optional[str] = Field(None, description="Glasses style of the avatar")
    eyebrowsStyle: Optional[str] = Field(None, description="Eyebrows style of the avatar")
    speakSpeed: Optional[int] = Field(None, description="Speed at which the avatar speaks")
    blinkSpeed: Optional[int] = Field(None, description="Speed at which the avatar blinks")

class Tools(BaseModel):
    search: Optional[Dict[str, str]] = Field(None, description="Tool for searching information with a description of the activity")
    scrape: Optional[Dict[str, str]] = Field(None, description="Tool for scraping data with a description of the activity")
    website_search: Optional[Dict[str, str]] = Field(None, description="Tool for querying a given website")
    pdf_reader: Optional[Dict[str, str]] = Field(None, description="Tool for reading PDF file contents")
    youtube_video_search: Optional[Dict[str, str]] = Field(None, description="Tool for querying the contents of a youtube video")
    query_visual_website: Optional[Dict[str, str]] = Field(None, description="Tool for querying a website url using vision")
    phone_call: Optional[Dict[str, Any]] = Field(None, description="Tool for having a conversation over a phone call with someone")
  
class ExpertModel(BaseModel):
    type: Optional[str] = Field(None, description="Type of the object, e.g., 'expert'")
    name: Optional[str] = Field(None, description="Name of the expert")
    age: Optional[int] = Field(None, description="Age of the expert")
    role: str = Field(..., description="Role of the expert, e.g., 'Designer'")
    goal: str = Field(..., description="Goal or objective of the expert")
    backstory: str = Field(..., description="Backstory of the expert detailing previous experiences and specializations")
    personality: Optional[str] = Field("", description="Personality of the expert, communication style, etc.")
    collaborate: bool = Field(..., description="Flag indicating whether the expert is open to collaboration")
    avatar: Optional[AvatarDetails] = Field(None, description="Detailed avatar settings of the expert")
    tools: Optional[Tools] = Field(None, description="Tools associated with the expert and their specific functions")
    avatar_id: str = Field(..., description="Identifier for the field associated with the avatar")
    study: Optional[List[str]] = Field(None, description="Optional list of URLs for learning resources related to the expert")
    max_execution_time: int = Field(..., description="Maximum number of seconds the expert can work on a task")
    max_num_iterations: Optional[int] = Field(7, description="Maximum number of iterations the expert can work on a task. More is smarter.")
    smart_level: Optional[int] = Field(2, description="Smartness level, from 1 to 3, being 1 the dumbest available (grok), 2 (gpt-4o), 3 the smartest available (gpt-4).")

class TaskContext(BaseModel):
    context: str = Field(..., description="The context of the task")
    schema: Optional[Dict] = Field(default=None, description="Optional and unrestricted schema dictionary")
    name: str = Field(..., description="The name of the task")
    task: str = Field(..., description="Description of the task")
    rules: Optional[str] = Field(None, description="Optional set of rules for the task")

class ImprovedTask(BaseModel): 
    description: str = Field(..., description="An easier and accurate description with fixed url schemas if needed, for the task to perform")
    description_first_person: str = Field(..., description="An easier to understand first person description for the task to perform, and as if you were the team leader in a meeting guiding others, using less than 140 characters")
    expected_output: str = Field(..., description="A description of the expected output for the task")
    coordinator_backstory: str = Field(..., description="A backstory description for a coordinator LLM agent specific for delegating this task")