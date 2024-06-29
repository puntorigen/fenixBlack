# Description: This file contains the messages that are sent to the frontend.
import json
from schemas import ExpertModel

class messages:
    def __init__(self, manager, session_id:str, expert:ExpertModel, meeting_id:str):
        self.session_id = session_id
        self.expert_id = expert.avatar_id
        self.expert_role = expert.role
        self.meeting_id = meeting_id
        self.manager = manager

    async def to_tool(self, cmd:str, data:dict):
        await self.manager.send_message(json.dumps({
            "cmd": cmd,
            "session_id": self.session_id,
            "data": data
        }), self.meeting_id)

    async def from_tool(self, tool_id, speak:str):
        await self.manager.send_message(json.dumps({
            "action": "reportAgentSteps",
            "session_id": self.session_id,
            "data": [],
            "expert_action": {
                "expert_id": self.expert_id,
                "kind": "tool",
                "speak": speak,
                "speak_raw": speak,
                "tool_id": tool_id,
                "tool_input": "",
                "valid": True
            },
            "expert_id": self.expert_id,
            "expert_role": self.expert_role
        }), self.meeting_id)