# 部署说明

项目使用根目录的 `docker-compose.yml` 编排 MySQL、FastAPI 后端和 Vue/Nginx 前端。

```powershell
docker compose up -d --build
```

生产环境部署时建议：

- 使用 `.env` 管理数据库密码、大模型 Key 和外部 API Key。
- MySQL 数据通过 `mysql_data` Docker volume 持久化。
- 后端上传图片通过 `backend_data` Docker volume 持久化。
- Nginx 前端容器负责静态资源托管和 `/api` 反向代理。
