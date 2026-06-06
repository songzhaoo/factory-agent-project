CREATE INDEX idx_orders_updated_at ON orders(updated_at);

CREATE INDEX idx_orders_status_due ON orders(status, due_date);

CREATE INDEX idx_tasks_order_seq ON production_tasks(order_id, process_seq);

CREATE INDEX idx_tasks_equipment_status ON production_tasks(equipment_code, current_status);

CREATE INDEX idx_inventory_material_spec ON inventory_items(material_name, spec);

CREATE INDEX idx_quality_status_updated ON quality_issues(status, updated_at);

CREATE INDEX idx_inventory_movements_item_time ON inventory_movements(inventory_id, created_at);
