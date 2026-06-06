CREATE TABLE IF NOT EXISTS inventory_movements (
    id VARCHAR(64) PRIMARY KEY,
    inventory_id VARCHAR(64),
    material_name VARCHAR(255) NOT NULL,
    movement_type VARCHAR(64) NOT NULL,
    qty_delta DOUBLE NOT NULL,
    qty_after DOUBLE NOT NULL,
    reference_type VARCHAR(64),
    reference_id VARCHAR(64),
    operator_name VARCHAR(100),
    remark TEXT,
    created_at VARCHAR(32) NOT NULL,
    CONSTRAINT fk_inventory_movements_item FOREIGN KEY(inventory_id) REFERENCES inventory_items(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
