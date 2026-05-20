# 模具制造与注塑生产协同 Agent

这是一个独立的前后端分离工程化项目，面向没有 ERP / MES 的塑胶制品厂、模具厂。

业务场景覆盖：

- 用深孔钻、车床、铣床、磨床、摇臂钻床、CNC、火花机、线切割加工铁模具。
- 模具完成后进入试模和注塑机生产。
- 产品包括汽车配件、彩电/冰箱/洗衣机塑胶件、水壶、茶杯等塑胶或五金成品。
- 车间师傅通过手机扫码报工更新任务状态。
- Agent 调用工具查询数据库和外部公开 API，回答生产进度、设备排产、注塑进度、质检异常、库存、天气、多模态识别和延期风险。

## 技术栈

- 后端：FastAPI + MySQL + OpenPyXL
- 前端：Vue 3 + Vite + Nginx
- Agent：工具调用框架，支持 DashScope / Qwen tool calling；未配置 Key 时自动使用本地规则路由
- 多模态：支持 DashScope / Qwen-VL 图片识别；未配置 Key 时自动使用本地规则识别
- 部署：Docker Compose

## 功能

## 工程目录

```text
factory-agent-project/
  backend/                    后端工程
    app/
      api/
        routes.py             FastAPI 路由层，负责 HTTP 入参、状态码和接口返回
      core/
        config.py             全局配置
        logging.py            日志配置
      db/
        database.py           MySQL 连接、建表和演示数据初始化
      schemas/
        models.py             Pydantic 请求/响应模型
      services/
        factory.py            业务服务层，包含生产数据服务和 Agent 工具编排
      main.py                 应用工厂，挂载中间件和 API Router
    Dockerfile                后端容器构建文件
    requirements.txt          Python 依赖

  frontend/                   前端工程
    src/
      api/
        client.js             前端 API client
      components/
        AppHeader.vue         顶部栏组件
        SummaryGrid.vue       统计卡片组件
      constants/
        factory.js            业务常量和选项配置
      styles/
        styles.css            页面样式
      App.vue                 Vue 单文件组件，承载主工作台和扫码报工页面
      main.js                 Vue 应用启动入口
    index.html                Vite HTML 挂载入口
    vite.config.js            Vite 开发代理和构建配置
    package.json              Vue 3 + Vite 工程配置
    nginx.conf                静态资源托管和 /api 反向代理
    Dockerfile                前端容器构建文件

  deploy/                     部署说明和上线配置说明
  docs/                       项目流程图、面试问答和说明文档
  scripts/                    启动、停止和健康检查脚本
  tests/                      测试目录说明和后续自动化测试入口
  docker-compose.yml          编排 MySQL、后端和前端服务
  .env.example                环境变量模板，不包含真实密钥
  README.md                   项目说明
```

### 1. 完整工序流转

内置工序：

```text
深孔钻 → 车床 → 铣床 → 磨床 → 摇臂钻床 → CNC加工 → 火花机 → 线切割 → 钳工装配 → 试模 → 注塑生产 → 质检 → 包装出货
```

### 2. 数据模块

- 订单表
- 模具表
- 设备表
- 工序任务表
- 扫码报工记录表
- 注塑生产表
- 质检异常表
- 库存表
- Excel / CSV 导入记录表
- Agent 工具调用日志表

### 3. 手机扫码报工

每个订单都有报工链接：

```text
http://127.0.0.1:8900/work-report?order_id=ORD-001
```

前端订单列表支持点击“二维码”按钮，将订单报工链接生成可视化二维码。车间师傅扫码进入订单报工页后，可以在页面里选择具体工序，再提交报工。这样现场只需要给每个订单贴一个二维码，不需要每道工序单独贴码。

师傅可以提交：

- 开始加工
- 加工完成
- 异常暂停
- 操作人
- 备注

提交后后端实时更新数据库。Agent 查询的是数据库最新状态，不靠模型猜。

### 4. Excel / CSV 导入

前端支持上传 `.xlsx` 或 `.csv`。

导入类型：

- `orders`：订单表
- `tasks`：工序任务表
- `inventory`：库存表
- `quality`：质检异常表

### 5. 车间单据与现场图片识别

前端支持拍照或上传图片资料，手机端会优先唤起摄像头，选择图片后可先预览，再提交识别：

- 单据识别：采购单、送货单、质检单、纸质报工单
- 质检图片分析：缩水、毛边、划痕、色差、变形等缺陷图片
- 设备现场识别：设备铭牌、设备面板、报警界面
- 库存标签盘点：物料标签、托盘标签、包装袋标签
- 图纸/工艺单理解：模具图纸截图、工艺单、加工要求

如果配置了 `DASHSCOPE_API_KEY`，会优先调用 Qwen-VL 多模态模型识别图片；如果没有配置或调用失败，则使用本地规则根据图片类型、文件名和备注生成结构化候选结果，保证功能可演示。

### 6. Agent 工具

Agent 内置工具：

- `query_order_progress`：查询订单和模具整体进度
- `query_process_tasks`：查询深孔钻、车床、铣床、磨床、摇臂钻床、CNC、火花机、线切割、注塑等工序任务
- `query_equipment_schedule`：查询设备排产和设备当前任务
- `query_injection_runs`：查询注塑机生产进度
- `query_quality_issues`：查询质检异常
- `query_inventory`：查询库存
- `query_weather`：调用 Open-Meteo 免费天气 API，判断出货、送货和外发加工天气风险
- `query_logistics`：调用快递鸟接口查询物流轨迹、签收状态和异常节点
- `query_route_plan`：调用高德地图 Web 服务查询送货距离和预计运输时长
- `query_web_search`：调用 Tavily 查询外部公开资料、行业信息和材料行情
- `query_workday_calendar`：调用节假日 API 判断交期是否遇到节假日、周末或调休
- `query_multimodal_records`：查询多模态图片识别记录，包括单据、质检缺陷图、设备报警图、库存标签和工艺图纸
- `generate_delay_risk_report`：生成延期风险报告

如果配置了 `DASHSCOPE_API_KEY`，会优先让 Qwen 选择工具；如果没有配置，则使用本地规则选择工具，项目仍然可以完整演示。物流、路线、联网搜索、节假日工具需要分别配置对应平台的 Key。

## 启动

在本目录运行：

```bash
docker compose up -d --build
```

访问前端：

```text
http://127.0.0.1:8900
```

访问后端：

```text
http://127.0.0.1:8901/api/health
```

手机报工页：

```text
http://127.0.0.1:8900/work-report?task_id=10086
```

## 配置大模型

项目默认使用 Docker Compose 启动 MySQL。`.env` 中可配置数据库账号和外部接口 Key：

```env
MYSQL_ROOT_PASSWORD=你的MySQLRoot密码
MYSQL_DATABASE=factory_agent
MYSQL_USER=factory_agent
MYSQL_PASSWORD=你的MySQL业务账号密码
DASHSCOPE_API_KEY=你的DashScopeKey
DASHSCOPE_MODEL=qwen-turbo
DASHSCOPE_VL_MODEL=qwen-vl-plus
KDNIAO_EBUSINESS_ID=你的快递鸟用户ID
KDNIAO_API_KEY=你的快递鸟APIKey
KDNIAO_REQUEST_TYPE=8002
AMAP_KEY=你的高德Web服务Key
TAVILY_API_KEY=你的TavilyKey
JIEJIARI_API_KEY=你的节假日APIKey
DEFAULT_FACTORY_ADDRESS=深圳
LOG_LEVEL=INFO
```

MySQL 会通过 `mysql_data` 数据卷持久化数据；后端上传图片仍保存在 `backend_data` 数据卷。

然后重启：

```bash
docker compose up -d --build
```

## 日志

后端默认输出结构化文本日志到容器标准输出，包含请求方法、路径、状态码、耗时、报工提交、数据导入、Agent 工具选择和外部 API 调用异常。

查看日志：

```bash
docker compose logs -f backend
```

可通过 `.env` 调整日志等级：

```env
LOG_LEVEL=DEBUG
```

## 可测试问题

```text
洗衣机面板模具 CNC 做完了吗
深孔钻、车床、铣床、磨床这些工序现在进度怎么样
CNC 今天有哪些任务
注塑机现在生产什么
ABS 和 PP 库存够不够
今天有哪些质检异常
哪些任务有延期风险
明天深圳下雨吗，会不会影响出货
最近上传的图片识别记录有哪些
这张质检缺陷图识别出了什么问题
设备报警图片会不会影响排产
```

## 面试说法

这个项目面向没有 ERP / MES 的中小型塑胶制品和模具制造工厂。项目没有假设企业已有完整系统，而是先通过 Excel 导入初始化订单、工序、库存、质检等数据，再通过手机扫码报工实时更新工序状态。用户提问后，Agent 先做意图识别，判断问题属于订单进度、工序设备、库存、质检、天气、物流、路线、节假日还是多模态记录；随后做槽位抽取和槽位填充，提取订单号、产品名、模具名、工序名、城市、日期、起点终点、快递公司、物流单号等参数，缺失参数优先从上下文补齐，补不齐则提示用户补充。最后调用订单进度、设备排产、注塑生产、质检异常、库存、天气、物流、路线、节假日、联网搜索和延期风险等工具，从数据库或外部 API 读取真实数据，再整理成自然语言回答。
