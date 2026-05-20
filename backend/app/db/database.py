from __future__ import annotations

import logging
import os
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Iterator

try:
    import pymysql
    from pymysql.cursors import DictCursor
except ModuleNotFoundError:
    pymysql = None
    DictCursor = None


EQUIPMENT = [
    ("DH-01", "深孔钻", "深孔钻-01"),
    ("LATHE-01", "车床", "车床-01"),
    ("MILL-01", "铣床", "铣床-01"),
    ("GRIND-01", "磨床", "磨床-01"),
    ("RADIAL-01", "摇臂钻床", "摇臂钻床-01"),
    ("CNC-01", "CNC", "CNC-01"),
    ("CNC-02", "CNC", "CNC-02"),
    ("EDM-01", "火花机", "火花机-01"),
    ("WIRE-01", "线切割", "线切割-01"),
    ("INJ-01", "注塑机", "注塑机-01"),
    ("INJ-02", "注塑机", "注塑机-02"),
]

logger = logging.getLogger(__name__)


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def dt_text(days: int = 0, hours: int = 0) -> str:
    return (datetime.now() + timedelta(days=days, hours=hours)).strftime("%Y-%m-%d %H:%M:%S")


class MySQLConnectionAdapter:
    def __init__(self, connection: Any) -> None:
        self.connection = connection

    def execute(self, sql: str, params: tuple[Any, ...] | list[Any] = ()) -> Any:
        cursor = self.connection.cursor()
        cursor.execute(sql.replace("?", "%s"), params)
        return cursor

    def executescript(self, script: str) -> None:
        for statement in [item.strip() for item in script.split(";") if item.strip()]:
            self.execute(statement)

    def commit(self) -> None:
        self.connection.commit()

    def rollback(self) -> None:
        self.connection.rollback()

    def close(self) -> None:
        self.connection.close()


class Database:
    def __init__(self) -> None:
        logger.info(
            "database_initializing driver=mysql host=%s port=%s database=%s",
            os.getenv("MYSQL_HOST", "mysql"),
            os.getenv("MYSQL_PORT", "3306"),
            os.getenv("MYSQL_DATABASE", "factory_agent"),
        )
        self.init_schema()
        self.seed_demo_data()

    @contextmanager
    def connect(self) -> Iterator[MySQLConnectionAdapter]:
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _connect(self) -> MySQLConnectionAdapter:
        if pymysql is None or DictCursor is None:
            raise RuntimeError("当前环境缺少 pymysql，无法连接 MySQL")
        last_error: Exception | None = None
        for _ in range(30):
            try:
                connection = pymysql.connect(
                    host=os.getenv("MYSQL_HOST", "mysql"),
                    port=int(os.getenv("MYSQL_PORT", "3306")),
                    user=os.getenv("MYSQL_USER", "factory_agent"),
                    password=os.getenv("MYSQL_PASSWORD", "factory_agent_pass"),
                    database=os.getenv("MYSQL_DATABASE", "factory_agent"),
                    charset="utf8mb4",
                    cursorclass=DictCursor,
                    autocommit=False,
                )
                return MySQLConnectionAdapter(connection)
            except Exception as exc:
                last_error = exc
                time.sleep(1)
        raise RuntimeError(f"MySQL 连接失败：{last_error}") from last_error

    def init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(MYSQL_SCHEMA)

    def seed_demo_data(self) -> None:
        with self.connect() as conn:
            exists = conn.execute("SELECT id FROM production_tasks WHERE id = ?", ("10086",)).fetchone()
            if exists:
                logger.info("demo_data_seed_skipped reason=existing_task task_id=10086")
                return
            now = now_text()
            customer_id = "CUST-001"
            order_id = "ORD-001"
            mold_id = "MOLD-001"
            conn.execute("INSERT INTO customers VALUES (?, ?, ?, ?)", (customer_id, "华南家电客户", "李经理", now))
            conn.execute(
                """
                INSERT INTO orders
                (id, customer_id, order_no, product_name, product_type, quantity, due_date, status, priority, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (order_id, customer_id, "SO20260513001", "洗衣机面板", "家用电器塑胶件", 5000, dt_text(days=7), "生产中", "加急", now, now),
            )
            conn.execute(
                """
                INSERT INTO molds
                (id, order_id, mold_no, mold_name, material, current_stage, status, owner_name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (mold_id, order_id, "MJ-WM-001", "洗衣机面板模具", "P20模具钢", "CNC加工", "加工中", "张师傅", now, now),
            )
            for code, equipment_type, name in EQUIPMENT:
                conn.execute(
                    """
                    INSERT INTO equipment (id, code, equipment_type, name, status, operator_name, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (new_id("EQ"), code, equipment_type, name, "运行中" if code == "CNC-01" else "空闲", "张师傅" if code == "CNC-01" else "", now, now),
                )
            demo_tasks = [
                ("10081", "深孔钻", "DH-01", "已完成", "王师傅", -2, -2),
                ("10082", "车床", "LATHE-01", "已完成", "赵师傅", -2, -1),
                ("10083", "铣床", "MILL-01", "已完成", "陈师傅", -1, -1),
                ("10084", "磨床", "GRIND-01", "已完成", "周师傅", -1, 0),
                ("10085", "摇臂钻床", "RADIAL-01", "已完成", "刘师傅", 0, 0),
                ("10086", "CNC加工", "CNC-01", "加工中", "张师傅", 0, 1),
                ("10087", "火花机", "EDM-01", "未开始", "黄师傅", 1, 2),
                ("10088", "线切割", "WIRE-01", "未开始", "吴师傅", 2, 3),
                ("10089", "钳工装配", "CNC-02", "未开始", "郑师傅", 3, 4),
                ("10090", "试模", "INJ-01", "未开始", "何师傅", 4, 5),
                ("10091", "注塑生产", "INJ-01", "未开始", "马师傅", 5, 6),
                ("10092", "质检", "INJ-02", "未开始", "质检员A", 6, 7),
            ]
            for seq, (task_id, process_name, equipment_code, status, owner, start_day, end_day) in enumerate(demo_tasks, start=1):
                actual_start = dt_text(days=start_day) if status in {"已完成", "加工中"} else None
                actual_finish = dt_text(days=end_day) if status == "已完成" else None
                conn.execute(
                    """
                    INSERT INTO production_tasks
                    (id, order_id, mold_id, product_name, process_name, process_seq, equipment_code, current_status, owner_name,
                     planned_start_at, planned_end_at, actual_start_at, actual_finish_at, remark, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task_id,
                        order_id,
                        mold_id,
                        "洗衣机面板模具" if process_name != "注塑生产" else "洗衣机面板塑胶件",
                        process_name,
                        seq,
                        equipment_code,
                        status,
                        owner,
                        dt_text(days=start_day),
                        dt_text(days=end_day),
                        actual_start,
                        actual_finish,
                        "演示任务：扫码后可提交开始、完成或异常暂停" if task_id == "10086" else "",
                        now,
                        now,
                    ),
                )
            conn.execute(
                "INSERT INTO work_reports (id, task_id, action, status_after, operator_name, remark, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (uuid.uuid4().hex, "10086", "初始化", "加工中", "系统", "初始化演示任务", now),
            )
            conn.execute(
                """
                INSERT INTO injection_runs
                (id, order_id, product_name, machine_code, material_name, plan_qty, completed_qty, bad_qty, status, started_at, estimated_finish_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (new_id("INJ"), order_id, "洗衣机面板塑胶件", "INJ-01", "ABS", 5000, 0, 0, "待生产", None, dt_text(days=7), now),
            )
            conn.execute(
                """
                INSERT INTO quality_issues
                (id, order_id, product_name, issue_type, bad_qty, cause, status, owner_name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (new_id("QI"), order_id, "水壶外壳", "缩水", 36, "保压时间不足，需复核注塑参数", "处理中", "质检员A", now, now),
            )
            for material_name, spec, unit, qty, safety_qty, supplier, eta in [
                ("ABS", "奇美PA-757", "kg", 820, 500, "华南塑胶", dt_text(days=2)),
                ("PP", "食品级PP", "kg", 180, 300, "东莞材料商", dt_text(days=1)),
                ("P20模具钢", "60*800*1200", "块", 3, 2, "钢材供应商", ""),
            ]:
                conn.execute(
                    """
                    INSERT INTO inventory_items
                    (id, material_name, spec, unit, qty, safety_qty, supplier, eta, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (new_id("INV"), material_name, spec, unit, qty, safety_qty, supplier, eta, now),
                )
            logger.info("demo_data_seeded order_id=%s mold_id=%s", order_id, mold_id)


MYSQL_SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    contact VARCHAR(255),
    created_at VARCHAR(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS orders (
    id VARCHAR(64) PRIMARY KEY,
    customer_id VARCHAR(64),
    order_no VARCHAR(100) NOT NULL UNIQUE,
    product_name VARCHAR(255) NOT NULL,
    product_type VARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    due_date VARCHAR(32) NOT NULL,
    status VARCHAR(64) NOT NULL,
    priority VARCHAR(64) NOT NULL DEFAULT '普通',
    created_at VARCHAR(32) NOT NULL,
    updated_at VARCHAR(32) NOT NULL,
    CONSTRAINT fk_orders_customer FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS molds (
    id VARCHAR(64) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    mold_no VARCHAR(100) NOT NULL UNIQUE,
    mold_name VARCHAR(255) NOT NULL,
    material VARCHAR(255),
    current_stage VARCHAR(100) NOT NULL,
    status VARCHAR(64) NOT NULL,
    owner_name VARCHAR(100),
    created_at VARCHAR(32) NOT NULL,
    updated_at VARCHAR(32) NOT NULL,
    CONSTRAINT fk_molds_order FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS equipment (
    id VARCHAR(64) PRIMARY KEY,
    code VARCHAR(100) NOT NULL UNIQUE,
    equipment_type VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(64) NOT NULL DEFAULT '空闲',
    operator_name VARCHAR(100),
    created_at VARCHAR(32) NOT NULL,
    updated_at VARCHAR(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS production_tasks (
    id VARCHAR(64) PRIMARY KEY,
    order_id VARCHAR(64),
    mold_id VARCHAR(64),
    product_name VARCHAR(255) NOT NULL,
    process_name VARCHAR(100) NOT NULL,
    process_seq INT NOT NULL,
    equipment_code VARCHAR(100) NOT NULL,
    current_status VARCHAR(64) NOT NULL,
    owner_name VARCHAR(100) NOT NULL,
    planned_start_at VARCHAR(32),
    planned_end_at VARCHAR(32),
    actual_start_at VARCHAR(32),
    actual_finish_at VARCHAR(32),
    remark TEXT,
    created_at VARCHAR(32) NOT NULL,
    updated_at VARCHAR(32) NOT NULL,
    CONSTRAINT fk_tasks_order FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE SET NULL,
    CONSTRAINT fk_tasks_mold FOREIGN KEY(mold_id) REFERENCES molds(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS work_reports (
    id VARCHAR(64) PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL,
    action VARCHAR(64) NOT NULL,
    status_after VARCHAR(64) NOT NULL,
    operator_name VARCHAR(100),
    remark TEXT,
    created_at VARCHAR(32) NOT NULL,
    CONSTRAINT fk_reports_task FOREIGN KEY(task_id) REFERENCES production_tasks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS injection_runs (
    id VARCHAR(64) PRIMARY KEY,
    order_id VARCHAR(64),
    product_name VARCHAR(255) NOT NULL,
    machine_code VARCHAR(100) NOT NULL,
    material_name VARCHAR(255) NOT NULL,
    plan_qty INT NOT NULL,
    completed_qty INT NOT NULL DEFAULT 0,
    bad_qty INT NOT NULL DEFAULT 0,
    status VARCHAR(64) NOT NULL,
    started_at VARCHAR(32),
    estimated_finish_at VARCHAR(32),
    updated_at VARCHAR(32) NOT NULL,
    CONSTRAINT fk_injection_order FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS quality_issues (
    id VARCHAR(64) PRIMARY KEY,
    order_id VARCHAR(64),
    product_name VARCHAR(255) NOT NULL,
    issue_type VARCHAR(100) NOT NULL,
    bad_qty INT NOT NULL,
    cause TEXT,
    status VARCHAR(64) NOT NULL,
    owner_name VARCHAR(100),
    created_at VARCHAR(32) NOT NULL,
    updated_at VARCHAR(32) NOT NULL,
    CONSTRAINT fk_quality_order FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS inventory_items (
    id VARCHAR(64) PRIMARY KEY,
    material_name VARCHAR(255) NOT NULL,
    spec VARCHAR(255),
    unit VARCHAR(32) NOT NULL DEFAULT 'kg',
    qty DOUBLE NOT NULL,
    safety_qty DOUBLE NOT NULL,
    supplier VARCHAR(255),
    eta VARCHAR(32),
    updated_at VARCHAR(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS multimodal_records (
    id VARCHAR(64) PRIMARY KEY,
    category VARCHAR(64) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100),
    storage_path VARCHAR(500),
    file_size INT NOT NULL,
    description TEXT,
    extracted_json JSON NOT NULL,
    analysis TEXT NOT NULL,
    suggestions TEXT NOT NULL,
    source VARCHAR(100) NOT NULL,
    created_at VARCHAR(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS import_batches (
    id VARCHAR(64) PRIMARY KEY,
    data_type VARCHAR(64) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    total_rows INT NOT NULL,
    success_rows INT NOT NULL,
    error_rows INT NOT NULL,
    created_at VARCHAR(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS agent_tool_logs (
    id VARCHAR(64) PRIMARY KEY,
    question TEXT NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    arguments_json JSON NOT NULL,
    created_at VARCHAR(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""
