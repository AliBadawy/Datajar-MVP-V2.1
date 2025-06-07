from pydantic import BaseModel
from typing import List, Dict, Optional

class GoogleAnalyticsRequest(BaseModel):
    service_account_json: dict  # parsed JSON from frontend
    property_id: str
    start_date: str  # format: YYYY-MM-DD
    end_date: str
    metrics: List[str]

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
    user_id: Optional[str] = None  # Supabase user ID for row-level security

class ProjectResponse(ProjectCreateRequest):
    id: int
    created_at: str
    user_id: Optional[str] = None  # Ensure user_id is included in responses

class SallaOrdersRequest(BaseModel):
    access_token: str
    from_date: str  # e.g. "2024-01-01"
    to_date: str    # e.g. "2024-01-31"
    project_id: int  # Associate with a specific project
