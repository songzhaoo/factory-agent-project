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
