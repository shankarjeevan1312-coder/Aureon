import json
import logging
from typing import Dict, Any, Callable, Optional, Awaitable
from pydantic import BaseModel

logger = logging.getLogger("aureon.tools")

class ToolResult(BaseModel):
    tool_name: str
    success: bool
    output: Any
    requires_confirmation: bool = False
    confirmation_prompt: Optional[str] = None
    voice_summary: Optional[str] = None

class BaseTool:
    def __init__(self, name: str, description: str, is_destructive: bool = False, requires_confirmation: bool = False):
        self.name = name
        self.description = description
        self.is_destructive = is_destructive
        self.requires_confirmation = requires_confirmation or is_destructive

    async def execute(self, **kwargs) -> ToolResult:
        raise NotImplementedError

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self.tools.get(name)

    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        return {
            name: {
                "description": tool.description,
                "is_destructive": tool.is_destructive,
                "requires_confirmation": tool.requires_confirmation
            }
            for name, tool in self.tools.items()
        }

    async def run_tool(self, name: str, args: Dict[str, Any], confirmed: bool = False) -> ToolResult:
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                tool_name=name,
                success=False,
                output=f"Tool '{name}' is not registered.",
                voice_summary=f"Unknown tool requested: {name}."
            )

        # Destructive safety check
        if tool.requires_confirmation and not confirmed:
            prompt = (
                f"Destructive action detected: {tool.name}. "
                f"Target parameters: {json.dumps(args)}. "
                "This cannot be undone. Do you confirm execution?"
            )
            return ToolResult(
                tool_name=name,
                success=False,
                output="Operation quarantined pending user confirmation.",
                requires_confirmation=True,
                confirmation_prompt=prompt,
                voice_summary="This action requires confirmation before proceeding."
            )

        try:
            return await tool.execute(**args)
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return ToolResult(
                tool_name=name,
                success=False,
                output=str(e),
                voice_summary=f"An error occurred while executing {name}."
            )

registry = ToolRegistry()
