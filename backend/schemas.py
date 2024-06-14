from typing import Dict, Optional
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
    search: Dict[str, str] = Field(..., description="Tool for searching information with a description of the activity")
    scrape: Dict[str, str] = Field(..., description="Tool for scraping data with a description of the activity")

class ExpertModel(BaseModel):
    type: Optional[str] = Field(None, description="Type of the object, e.g., 'expert'")
    name: str = Field(..., description="Name of the expert")
    age: Optional[int] = Field(None, description="Age of the expert")
    role: str = Field(..., description="Role of the expert, e.g., 'Designer'")
    goal: str = Field(..., description="Goal or objective of the expert")
    backstory: str = Field(..., description="Backstory of the expert detailing previous experiences and specializations")
    personality: Optional[str] = Field("", description="Personality of the expert, communication style, etc.")
    collaborate: bool = Field(..., description="Flag indicating whether the expert is open to collaboration")
    avatar: Optional[AvatarDetails] = Field(None, description="Detailed avatar settings of the expert")
    tools: Tools = Field(..., description="Tools associated with the expert and their specific functions")
    avatar_id: str = Field(..., description="Identifier for the field associated with the avatar")

class TaskContext(BaseModel):
    context: str = Field(..., description="The context of the task")
    schema: Optional[Dict] = Field(default=None, description="Optional and unrestricted schema dictionary")
    name: str = Field(..., description="The name of the task")
    task: str = Field(..., description="Description of the task")

class ImprovedTask(BaseModel):
    description: str = Field(..., description="An easier to understand description for the task to perform")
    expected_output: str = Field(..., description="A description of the expected output for the task")
    coordinator_backstory: str = Field(..., description="A backstory description for a coordinator LLM agent specific for delegating this task")