# 测试目录

当前项目包含后端单元测试和部署冒烟检查。

测试结构：

```text
tests/
  backend/      业务状态机、Agent 工具、数据导入、迁移辅助逻辑测试
  frontend/     Vue 页面交互和多模态上传测试
  integration/  Docker Compose 集成测试
```

后端自动化测试：

```powershell
cd backend
pip install -r requirements-dev.txt
cd ..
pytest tests/backend
```

当前可执行的冒烟检查：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/healthcheck.ps1
```
