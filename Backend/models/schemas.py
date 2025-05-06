from pydantic import BaseModel
from typing import List, Dict, Optional

class AnalyzeRequest(BaseModel):
    messages: List[Dict[str, str]]  # Expected format: [{ role: 'user', content: '...' }]
