from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class ColumnSchema(BaseModel):
    name: str
    data_type: str
    is_nullable: bool

class TableSchema(BaseModel):
    table_name: str
    columns: List[ColumnSchema]
    profiling_results: Optional[List['ProfilingResult']] = None

class ProfilingResult(BaseModel):
    table_name: str
    column_name: Optional[str] = None
    row_count: int
    null_count: Optional[int] = None
    distinct_count: Optional[int] = None

class TestCase(BaseModel):
    table_name: str
    test_name: str
    sql: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class RuleDefinition(BaseModel):
    id: str
    table_name: str
    rule_type: str
    severity: str
    owner: str
    dimension: str
    sql: str
    enabled: bool = True
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TestResult(BaseModel):
    table_name: str
    test_name: str
    sql: str
    failed_rows: int
    execution_time: float
    status: str # "PASSED" or "FAILED"
    error_category: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

class AnalysisResult(BaseModel):
    test_name: str
    table_name: str
    findings: str
    suggested_investigation: str
