from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class ColumnProfile(BaseModel):
    name: str
    inferred_type: str
    total_rows: int
    missing_count: int
    missing_ratio: float
    unique_count: int
    unique_ratio: float
    
    stats: Dict[str, Any] = {}

class DataIssue(BaseModel):
    type: str
    column: str
    severity: float = Field(ge=0.0, le=1.0)  
    confidence: float = Field(default=1.0)
    detail: str
    action: str  
    metadata: Dict[str, Any] = {}

class DatasetProfile(BaseModel):
    row_count: int
    column_count: int
    columns: Dict[str, ColumnProfile]
    duplicate_rows: Optional[int] = None

    issues: List[DataIssue] = []


