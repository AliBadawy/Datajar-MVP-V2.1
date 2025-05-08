from pydantic import BaseModel
from typing import List, Dict, Optional

class AnalyzeRequest(BaseModel):
    messages: List[Dict[str, str]]  # Expected format: [{ role: 'user', content: '...' }]
    dataframe: Optional[Dict] = None
    persona: Optional[str] = "Data Analyst"
    industry: Optional[str] = "E-Commerce"
    business_context: Optional[str] = ""
    project_id: Optional[int] = None  # Add project_id field to support project tracking

class ProjectCreateRequest(BaseModel):
    name: str
    persona: str
    context: str
    industry: str

class ProjectResponse(ProjectCreateRequest):
    id: int
    created_at: str

class SallaOrdersRequest(BaseModel):
    access_token: str
    from_date: str  # e.g. "2024-01-01"
    to_date: str    # e.g. "2024-01-31"
    project_id: int  # Associate with a specific project
