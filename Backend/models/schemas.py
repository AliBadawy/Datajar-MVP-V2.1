from pydantic import BaseModel
from typing import List, Dict, Optional

class AnalyzeRequest(BaseModel):
    messages: List[Dict[str, str]]  # Expected format: [{ role: 'user', content: '...' }]
    dataframe: Optional[Dict] = None
    persona: Optional[str] = "Data Analyst"
    industry: Optional[str] = "E-Commerce"
    business_context: Optional[str] = ""

class ProjectCreateRequest(BaseModel):
    name: str
    persona: str
    context: str
    industry: str

class ProjectResponse(ProjectCreateRequest):
    id: int
    created_at: str
