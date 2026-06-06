# 数据库迁移

迁移文件按文件名顺序执行，并记录到 `schema_migrations` 表。

命名规则：

```text
001_initial_schema.sql
002_inventory_movements.sql
003_common_indexes.sql
```

新增表、字段或索引时，新建下一个编号的 SQL 文件，不要直接改已经上线执行过的迁移文件。

应用启动时会自动执行未应用的迁移。也可以在后端容器或后端工作目录里手动执行：

```bash
python -m app.db.migrate
```
