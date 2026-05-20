from __future__ import annotations

from pydantic import BaseModel, Field


class Customer(BaseModel):
    id: str
    name: str
    contact: str | None = None
    created_at: str


class Order(BaseModel):
    id: str
    customer_id: str | None = None
    order_no: str
    product_name: str
    product_type: str
    quantity: int
    due_date: str
    status: str
    priority: str = "普通"
    created_at: str
    updated_at: str
    report_url: str | None = None


class Mold(BaseModel):
    id: str
    order_id: str
    mold_no: str
    mold_name: str
    material: str | None = None
    current_stage: str
    status: str
    owner_name: str | None = None
    created_at: str
    updated_at: str


class Equipment(BaseModel):
    id: str
    code: str
    equipment_type: str
    name: str
    status: str
    operator_name: str | None = None
    created_at: str
    updated_at: str


class ProductionTask(BaseModel):
    id: str
    order_id: str | None = None
    mold_id: str | None = None
    product_name: str
    process_name: str
    process_seq: int
    equipment_code: str
    current_status: str
    owner_name: str
    planned_start_at: str | None = None
    planned_end_at: str | None = None
    actual_start_at: str | None = None
    actual_finish_at: str | None = None
    remark: str | None = None
    created_at: str
    updated_at: str
    report_url: str | None = None


class WorkReportRecord(BaseModel):
    id: str
    task_id: str
    action: str
    status_after: str
    operator_name: str | None = None
    remark: str | None = None
    created_at: str


class TaskDetail(BaseModel):
    task: ProductionTask
    reports: list[WorkReportRecord] = Field(default_factory=list)


class WorkReportSubmit(BaseModel):
    action: str = Field(pattern=r"^(开始加工|加工完成|异常暂停)$")
    operator_name: str = Field(min_length=1, max_length=80)
    remark: str | None = Field(default=None, max_length=500)


class WorkReportResponse(BaseModel):
    message: str
    task: ProductionTask
    report: WorkReportRecord


class InjectionRun(BaseModel):
    id: str
    order_id: str | None = None
    product_name: str
    machine_code: str
    material_name: str
    plan_qty: int
    completed_qty: int
    bad_qty: int
    status: str
    started_at: str | None = None
    estimated_finish_at: str | None = None
    updated_at: str


class QualityIssue(BaseModel):
    id: str
    order_id: str | None = None
    product_name: str
    issue_type: str
    bad_qty: int
    cause: str | None = None
    status: str
    owner_name: str | None = None
    created_at: str
    updated_at: str


class InventoryItem(BaseModel):
    id: str
    material_name: str
    spec: str | None = None
    unit: str = "kg"
    qty: float
    safety_qty: float
    supplier: str | None = None
    eta: str | None = None
    updated_at: str


class MultimodalRecord(BaseModel):
    id: str
    category: str
    filename: str
    content_type: str | None = None
    storage_path: str | None = None
    file_size: int
    description: str | None = None
    extracted: dict = Field(default_factory=dict)
    analysis: str
    suggestions: str
    source: str
    created_at: str


class ImportResult(BaseModel):
    batch_id: str
    data_type: str
    total_rows: int
    success_rows: int
    error_rows: int
    errors: list[str] = Field(default_factory=list)


class AgentAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    context: dict = Field(default_factory=dict)


class AgentAskResponse(BaseModel):
    answer: str
    tool: str
    data: list[dict] = Field(default_factory=list)
    context: dict = Field(default_factory=dict)
    used_llm: bool = False


class DashboardSummary(BaseModel):
    order_count: int
    task_count: int
    running_task_count: int
    exception_count: int
    low_inventory_count: int
    overdue_risk_count: int
