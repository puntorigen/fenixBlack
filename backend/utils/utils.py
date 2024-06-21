from pydantic import BaseModel, Field, create_model
from typing import Any, Dict, List, Type, Optional
import re

class MyBaseModel(BaseModel):
    def model_dump(self):
        # Example implementation, customize it as needed
        return self.model_dump_json()

    # If you need to customize serialization further:
    def dict(self, **kwargs):
        # Customize the dict output if necessary
        return super().model_dump(**kwargs)

    def json(self, **kwargs):
        # Customize the JSON output if necessary
        return super().model_dump_json(**kwargs)

def json2pydantic(json_schema: Dict[str, Any]) -> Type[BaseModel]:
    def create_pydantic_model(schema: Dict[str, Any], model_name: str = "DynamicModel") -> Type[BaseModel]:
        fields = {}
        required_fields = schema.get('required', [])

        for prop_name, prop_info in schema['properties'].items():
            field_type = prop_info['type']
            field_description = prop_info.get('description', '')
            is_required = prop_name in required_fields

            if field_type == 'object':
                # Recursive call for nested objects
                nested_model = create_pydantic_model(prop_info, prop_name.capitalize())
                fields[prop_name] = (nested_model, Field(... if is_required else None, description=field_description))
            elif field_type == 'array':
                # Handle arrays, potentially with nested objects
                item_info = prop_info['items']
                if item_info['type'] == 'object':
                    item_model = create_pydantic_model(item_info, f"{prop_name.capitalize()}Item")
                    fields[prop_name] = (List[item_model], Field(... if is_required else None, description=field_description))
                else:
                    fields[prop_name] = (List[get_python_type(item_info['type'])], Field(... if is_required else None, description=field_description))
            else:
                # Simple types
                fields[prop_name] = (get_python_type(field_type), Field(... if is_required else None, description=field_description))

        return create_model(model_name, __base__=MyBaseModel, **fields)
        #return create_model(model_name, **fields)

    def get_python_type(js_type: str) -> Any:
        type_mapping = {
            'string': str,
            'number': float,
            'integer': int,
            'boolean': bool
        }
        return type_mapping.get(js_type, Any)

    return create_pydantic_model(json_schema)

#DynamicModel = json2pydantic(schema) 
#print(DynamicModel.schema_json(indent=2))

def extract_sections(text: str) -> dict:
    # Define the regular expression patterns to match each section
    thought_pattern = re.compile(r'Thought:\s*(.*?)(?=\nAction:|\Z)', re.DOTALL)
    action_pattern = re.compile(r'Action:\s*(.*?)(?=\nAction Input:|\Z)', re.DOTALL)
    action_input_pattern = re.compile(r'Action Input:\s*(.*?)(?=\n|\Z)', re.DOTALL)
    
    # Initialize the result dictionary
    result = {
        "Thought": None,
        "Action": None,
        "Action Input": None
    }
    
    # Search for each pattern in the given text
    thought_match = thought_pattern.search(text)
    action_match = action_pattern.search(text)
    action_input_match = action_input_pattern.search(text)
    
    # If matches are found, assign the extracted content to the corresponding dictionary keys
    if thought_match:
        result["Thought"] = thought_match.group(1).strip()
    if action_match:
        result["Action"] = action_match.group(1).strip()
    if action_input_match:
        result["Action Input"] = action_input_match.group(1).strip()
    
    return result