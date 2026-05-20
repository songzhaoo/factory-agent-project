# 测试目录

当前项目主要通过接口健康检查和页面访问检查验证部署结果。

后续可按下面结构补充自动化测试：

```text
tests/
  backend/      FastAPI 接口、Agent 工具、数据导入测试
  frontend/     Vue 页面交互和多模态上传测试
  integration/  Docker Compose 集成测试
```

当前可执行的冒烟检查：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/healthcheck.ps1
```
