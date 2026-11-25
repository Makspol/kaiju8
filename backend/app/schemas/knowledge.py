from typing import Any

from pydantic import BaseModel, Field


class CreateKnowledgeItemRequest(BaseModel):
    name: str
    content: str
    content_type: str = "text/plain"
    metadata: dict[str, Any] = Field(default_factory=dict)
