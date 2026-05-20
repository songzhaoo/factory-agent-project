from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas import (
    AgentAskRequest,
    AgentAskResponse,
    ImportResult,
    MultimodalRecord,
    TaskDetail,
    WorkReportResponse,
    WorkReportSubmit,
)
from app.services import FactoryAgentService, FactoryDataService


router = APIRouter(prefix="/api")


def create_api_router(data_service: FactoryDataService, agent_service: FactoryAgentService) -> APIRouter:
    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": "2.0.0"}

    @router.get("/dashboard")
    def dashboard() -> dict:
        return data_service.dashboard().model_dump()

    @router.get("/orders")
    def orders() -> list[dict]:
        return [item.model_dump() for item in data_service.list_orders()]

    @router.get("/molds")
    def molds() -> list[dict]:
        return [item.model_dump() for item in data_service.list_molds()]

    @router.get("/equipment")
    def equipment() -> list[dict]:
        return [item.model_dump() for item in data_service.list_equipment()]

    @router.get("/tasks")
    def tasks(order_id: str | None = None) -> list[dict]:
        return [item.model_dump() for item in data_service.list_tasks(order_id)]

    @router.get("/injection-runs")
    def injection_runs() -> list[dict]:
        return [item.model_dump() for item in data_service.list_injection_runs()]

    @router.get("/quality-issues")
    def quality_issues() -> list[dict]:
        return [item.model_dump() for item in data_service.list_quality_issues()]

    @router.get("/inventory")
    def inventory() -> list[dict]:
        return [item.model_dump() for item in data_service.list_inventory()]

    @router.get("/multimodal-records")
    def multimodal_records() -> list[dict]:
        return [item.model_dump() for item in data_service.list_multimodal_records()]

    @router.get("/tasks/{task_id}", response_model=TaskDetail)
    def get_task(task_id: str) -> TaskDetail:
        detail = data_service.get_task_detail(task_id)
        if detail is None:
            raise HTTPException(status_code=404, detail="没有找到该生产任务")
        return detail

    @router.post("/tasks/{task_id}/reports", response_model=WorkReportResponse)
    def submit_report(task_id: str, payload: WorkReportSubmit) -> WorkReportResponse:
        result = data_service.submit_report(task_id, payload)
        if result is None:
            raise HTTPException(status_code=404, detail="没有找到该生产任务")
        return result

    @router.post("/import/{data_type}", response_model=ImportResult)
    async def import_file(data_type: str, file: UploadFile = File(...)) -> ImportResult:
        if data_type not in {"orders", "tasks", "inventory", "quality"}:
            raise HTTPException(status_code=400, detail="导入类型只能是 orders、tasks、inventory、quality")
        content = await file.read()
        return data_service.import_table(data_type, file.filename or "upload.xlsx", content)

    @router.post("/multimodal/upload", response_model=MultimodalRecord)
    async def upload_multimodal(
        category: str = Form(...),
        description: str = Form(""),
        file: UploadFile = File(...),
    ) -> MultimodalRecord:
        content = await file.read()
        try:
            return data_service.create_multimodal_record(category, file.filename or "upload.png", file.content_type, content, description)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/agent/ask", response_model=AgentAskResponse)
    def ask_agent(payload: AgentAskRequest) -> AgentAskResponse:
        return agent_service.ask(payload.question, payload.context)

    return router
