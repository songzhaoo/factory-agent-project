from __future__ import annotations

import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.db.database import Database  # noqa: E402
from app.services.factory import FactoryAgentService, FactoryDataService  # noqa: E402


class FakeCursor:
    def __init__(self, one=None, all_rows=None):
        self.one = one
        self.all_rows = all_rows or []

    def fetchone(self):
        return self.one

    def fetchall(self):
        return self.all_rows


class FakeConnection:
    def __init__(self, previous_task=None, occupied_task=None, existing_index=None):
        self.previous_task = previous_task
        self.occupied_task = occupied_task
        self.existing_index = existing_index
        self.executed = []

    def execute(self, sql, params=()):
        self.executed.append((sql, params))
        normalized = " ".join(sql.split())
        if normalized.startswith("SHOW INDEX"):
            return FakeCursor(self.existing_index)
        if "process_seq <" in normalized:
            return FakeCursor(self.previous_task)
        if "current_status = ?" in normalized and "id != ?" in normalized:
            return FakeCursor(self.occupied_task)
        return FakeCursor()


def test_work_report_rejects_invalid_status_transition():
    service = object.__new__(FactoryDataService)
    task = {
        "id": "T-001",
        "order_id": None,
        "equipment_code": "CNC-01",
        "process_seq": 1,
        "current_status": "未开始",
    }

    with pytest.raises(ValueError, match="不能提交"):
        service._validate_work_report(FakeConnection(), task, "加工完成")


def test_work_report_rejects_start_when_previous_task_unfinished():
    service = object.__new__(FactoryDataService)
    task = {
        "id": "T-002",
        "order_id": "ORD-001",
        "equipment_code": "CNC-01",
        "process_seq": 2,
        "current_status": "未开始",
    }
    previous = {"id": "T-001", "process_name": "深孔钻", "current_status": "加工中"}

    with pytest.raises(ValueError, match="上一道工序"):
        service._validate_work_report(FakeConnection(previous_task=previous), task, "开始加工")


def test_import_validation_requires_business_columns():
    with pytest.raises(ValueError, match="缺少必要列"):
        FactoryDataService._validate_import_rows("inventory", [{"规格": "奇美PA-757"}])


def test_inventory_movement_is_written_as_audit_record():
    conn = FakeConnection()

    FactoryDataService._record_inventory_movement(
        conn,
        inventory_id="INV-001",
        material_name="ABS",
        movement_type="导入调整",
        qty_delta=20,
        qty_after=120,
        reference_type="import",
        reference_id=None,
        operator_name="系统导入",
        remark="单元测试",
        created_at="2026-05-22 10:00:00",
    )

    sql, params = conn.executed[0]
    assert "INSERT INTO inventory_movements" in sql
    assert params[1:6] == ("INV-001", "ABS", "导入调整", 20, 120)


def test_agent_large_result_set_requires_clarification():
    service = object.__new__(FactoryAgentService)
    service._find_subject = lambda question: {}
    rows = [{"id": str(index)} for index in range(31)]

    result = service._cap_agent_rows(rows, {"question": "查一下进度"}, "请补充订单号。")

    assert result == [{"needs_clarification": True, "message": "匹配到 31 条数据，范围过大。请补充订单号。"}]


def test_migration_runner_skips_existing_index():
    conn = FakeConnection(existing_index={"Key_name": "idx_orders_updated_at"})

    should_skip = Database._should_skip_existing_index(
        conn,
        "CREATE INDEX idx_orders_updated_at ON orders(updated_at)",
    )

    assert should_skip is True
