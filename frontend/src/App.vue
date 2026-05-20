<template>
  <div class="app-shell">
    <AppHeader />

    <main v-if="!isReportPage" class="dashboard">
      <SummaryGrid :items="summaryItems" :active-key="activeSummaryKey" @open="openSummary" />

      <section class="panel agent-panel">
        <div class="section-title">
          <h2>生产 Agent 问答</h2>
          <span>{{ llmBadge }}</span>
        </div>
        <form class="question-form" @submit.prevent="askCurrentQuestion">
          <input v-model="agentQuestion" placeholder="例如：洗衣机面板模具 CNC 做完了吗？" />
          <button type="submit">提问</button>
        </form>
        <div class="quick-questions">
          <button v-for="question in quickQuestions" :key="question.text" type="button" @click="askQuickQuestion(question.value)">
            {{ question.text }}
          </button>
        </div>
        <div class="answer-box">
          <template v-if="agentMessages.length">
            <div v-for="(message, index) in visibleAgentMessages" :key="index" :class="['chat-message', message.role]">
              <strong>{{ message.role === "user" ? "问题" : "回答" }}</strong>
              <pre>{{ message.content }}</pre>
            </div>
          </template>
          <template v-else>等待提问。</template>
        </div>
      </section>

      <section class="panel import-panel">
        <div class="section-title">
          <h2>Excel / CSV 导入</h2>
        </div>
        <form class="import-form" @submit.prevent="importFile">
          <select v-model="importType">
            <option value="orders">订单表</option>
            <option value="tasks">工序任务表</option>
            <option value="inventory">库存表</option>
            <option value="quality">质检异常表</option>
          </select>
          <input ref="importFileInput" type="file" accept=".xlsx,.csv" />
          <button type="submit">导入</button>
        </form>
        <p class="message">{{ importMessage }}</p>
      </section>

      <section class="panel import-panel">
        <div class="section-title">
          <h2>车间单据与现场图片识别</h2>
          <span>拍照 / 选图 / 识别</span>
        </div>
        <form class="multimodal-form" @submit.prevent="uploadMultimodal">
          <div class="multimodal-fields">
            <select v-model="multimodalCategory">
              <option v-for="item in multimodalCategories" :key="item.key" :value="item.key">{{ item.label }}</option>
            </select>
            <input v-model="multimodalDescription" placeholder="可填写订单号、设备号、缺陷现象或物料信息，便于结构化识别" />
          </div>

          <div class="photo-uploader">
            <input
              ref="multimodalFileInput"
              class="sr-only"
              type="file"
              accept="image/*,.jpg,.jpeg,.png,.webp,.bmp"
              capture="environment"
              @change="selectMultimodalFile"
            />
            <button type="button" class="secondary-button" @click="$refs.multimodalFileInput.click()">拍照 / 选图</button>
            <button v-if="multimodalPreviewUrl" type="button" class="secondary-button" @click="clearMultimodalFile">清除</button>
            <span class="file-name">{{ multimodalFileName || "未选择图片" }}</span>
            <div v-if="multimodalPreviewUrl" class="photo-preview">
              <img :src="multimodalPreviewUrl" alt="待识别图片预览" />
            </div>
          </div>

          <button type="submit">上传识别</button>
        </form>
        <p class="message">{{ multimodalMessage }}</p>
        <article v-if="lastMultimodalResult" ref="recognitionResult" class="recognition-result latest-result">
          <div class="result-header">
            <div>
              <span class="result-kicker">最新识别结果</span>
              <strong>{{ lastMultimodalResult.filename }}</strong>
            </div>
            <span class="status-pill">已识别</span>
          </div>
          <div class="result-meta">
            <span>类型：{{ categoryName(lastMultimodalResult.category) }}</span>
            <span>来源：{{ lastMultimodalResult.source }}</span>
            <span>时间：{{ lastMultimodalResult.created_at }}</span>
          </div>
          <div class="result-section">
            <strong>分析结论</strong>
            <p>{{ lastMultimodalResult.analysis }}</p>
          </div>
          <div class="result-section">
            <strong>结构化字段</strong>
            <dl class="field-list">
              <template v-for="([key, value]) in extractedEntries(lastMultimodalResult.extracted)" :key="key">
                <dt>{{ key }}</dt>
                <dd>{{ value }}</dd>
              </template>
            </dl>
          </div>
          <div class="result-section">
            <strong>处理建议</strong>
            <p>{{ lastMultimodalResult.suggestions }}</p>
          </div>
        </article>
      </section>

      <section class="tabbar">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          type="button"
          :class="{ active: activeTab === tab.key }"
          @click="selectTab(tab.key)"
        >
          {{ tab.label }}
        </button>
      </section>

      <section ref="dataPanel" class="panel data-panel">
        <div class="section-title">
          <h2>{{ activeTableName }}</h2>
          <button type="button" @click="refreshAll">刷新</button>
        </div>
        <div class="data-grid">
          <template v-if="activeRows.length">
            <article v-for="row in activeRows" :key="row.id || row.code || row.order_no || row.mold_no" class="data-card">
              <template v-if="activeTab === 'tasks'">
                <strong>{{ row.product_name }}</strong>
                <span>任务：{{ row.id }} · {{ row.process_name }} · {{ row.equipment_code }}</span>
                <span>
                  状态：<span :class="['status-pill', { danger: row.current_status === '异常暂停' }]">{{ row.current_status }}</span>
                  · 负责人：{{ row.owner_name }}
                </span>
                <span>计划：{{ row.planned_start_at || "待确认" }} - {{ row.planned_end_at || "待确认" }}</span>
                <div class="task-actions">
                  <a :href="orderReportUrl(row.order_id)" class="task-link">进入订单报工</a>
                </div>
              </template>

              <template v-else-if="activeTab === 'orders'">
                <strong>{{ row.order_no }}</strong>
                <span>{{ row.product_name }} · {{ row.quantity }}件</span>
                <span>交期：{{ row.due_date }} · 状态：{{ row.status }}</span>
                <div class="task-actions">
                  <button type="button" class="secondary-button" @click="openOrderQr(row)">二维码</button>
                  <a :href="row.report_url || orderReportUrl(row.id)" class="task-link">进入订单报工</a>
                </div>
              </template>

              <template v-else-if="activeTab === 'molds'">
                <strong>{{ row.mold_name }}</strong>
                <span>编号：{{ row.mold_no }} · 材料：{{ row.material || "" }}</span>
                <span>阶段：{{ row.current_stage }} · 状态：{{ row.status }}</span>
              </template>

              <template v-else-if="activeTab === 'equipment'">
                <strong>{{ row.name }}</strong>
                <span>{{ row.code }} · {{ row.equipment_type }}</span>
                <span>状态：{{ row.status }} · 操作员：{{ row.operator_name || "待确认" }}</span>
              </template>

              <template v-else-if="activeTab === 'injection'">
                <strong>{{ row.machine_code }}</strong>
                <span>{{ row.product_name }} · 材料：{{ row.material_name }}</span>
                <span>计划 {{ row.plan_qty }} · 完成 {{ row.completed_qty }} · 不良 {{ row.bad_qty }} · {{ row.status }}</span>
              </template>

              <template v-else-if="activeTab === 'quality'">
                <strong>{{ row.product_name }}</strong>
                <span>{{ row.issue_type }} · 不良 {{ row.bad_qty }}</span>
                <span>状态：{{ row.status }} · 原因：{{ row.cause || "待分析" }}</span>
              </template>

              <template v-else-if="activeTab === 'multimodal'">
                <strong>{{ row.filename }}</strong>
                <span>{{ categoryName(row.category) }} · {{ row.source }} · {{ row.created_at }}</span>
                <span>{{ row.analysis }}</span>
                <span>建议：{{ row.suggestions }}</span>
                <span>字段：{{ extractedText(row.extracted) }}</span>
              </template>

              <template v-else>
                <strong>{{ row.material_name }}</strong>
                <span>{{ row.spec || "" }} · {{ row.qty }}{{ row.unit }}</span>
                <span>安全库存：{{ row.safety_qty }}{{ row.unit }} · 供应商：{{ row.supplier || "" }}</span>
              </template>
            </article>
          </template>
          <p v-else>暂无数据。</p>
        </div>
      </section>
    </main>

    <main v-else class="report-page">
      <a class="back-link" href="/">返回工作台</a>
      <section class="panel mobile-report">
        <p class="eyebrow">扫码报工</p>
        <h2>{{ orderId ? "订单工序报工" : "生产任务报工" }}</h2>
        <label v-if="orderId">
          选择工序
          <select v-model="selectedTaskId" @change="loadReportTask">
            <option v-for="item in orderTasks" :key="item.id" :value="item.id">
              {{ item.process_seq }}. {{ item.process_name }} · {{ item.equipment_code }} · {{ item.current_status }}
            </option>
          </select>
        </label>
        <div class="task-detail">
          <template v-if="task">
            <strong>{{ task.product_name }}</strong>
            <span>任务编号：{{ task.id }}</span>
            <span>工序：{{ task.process_name }}</span>
            <span>设备：{{ task.equipment_code }}</span>
            <span>
              当前状态：<span :class="['status-pill', { danger: task.current_status === '异常暂停' }]">{{ task.current_status }}</span>
            </span>
            <span>负责人：{{ task.owner_name }}</span>
            <span>更新时间：{{ task.updated_at }}</span>
          </template>
          <template v-else>{{ taskMessage }}</template>
        </div>

        <label>
          操作人
          <input v-model="operatorName" placeholder="请输入操作人" />
        </label>

        <label>
          操作类型
          <select v-model="reportAction">
            <option value="开始加工">开始加工</option>
            <option value="加工完成">加工完成</option>
            <option value="异常暂停">异常暂停</option>
          </select>
        </label>

        <label>
          备注
          <textarea v-model="reportRemark" placeholder="例如：CNC加工完成，准备转火花机；或刀具异常暂停"></textarea>
        </label>

        <button type="button" @click="submitReport">提交报工</button>
        <p :class="['message', { error: reportError }]">{{ reportMessage }}</p>
      </section>

      <section class="panel mobile-report">
        <div class="section-title">
          <h2>最近报工记录</h2>
          <button type="button" @click="loadReportTask">刷新</button>
        </div>
        <div class="report-history">
          <template v-if="reports.length">
            <article v-for="item in reports" :key="item.id">
              <strong>{{ item.action }} · {{ item.status_after }}</strong>
              <span>{{ item.operator_name || "" }} · {{ item.created_at }}</span>
              <small>{{ item.remark || "" }}</small>
            </article>
          </template>
          <p v-else>暂无报工记录。</p>
        </div>
      </section>
    </main>

    <div v-if="qrDialog.visible" class="modal-mask" @click.self="closeReportQr">
      <section class="qr-dialog" role="dialog" aria-modal="true" aria-label="订单报工二维码">
        <div class="section-title">
          <h2>订单报工二维码</h2>
          <button type="button" class="secondary-button" @click="closeReportQr">关闭</button>
        </div>
        <div class="qr-body">
          <img v-if="qrDialog.imageUrl" :src="qrDialog.imageUrl" alt="订单报工二维码" />
          <p v-else class="message">{{ qrDialog.message || "二维码生成中..." }}</p>
        </div>
        <div class="qr-info">
          <strong>{{ qrDialog.title }}</strong>
          <span>{{ qrDialog.url }}</span>
        </div>
        <a class="header-link" :href="qrDialog.url">打开报工页面</a>
      </section>
    </div>
  </div>
</template>

<script>
import QRCode from "qrcode";
import { apiRequest } from "./api/client.js";
import AppHeader from "./components/AppHeader.vue";
import SummaryGrid from "./components/SummaryGrid.vue";
import { multimodalCategories, quickQuestions, tableNames, tabs } from "./constants/factory.js";

export default {
  name: "FactoryAgentApp",
  components: {
    AppHeader,
    SummaryGrid,
  },
  data() {
    return {
      isReportPage: window.location.pathname.startsWith("/work-report"),
      activeTab: "tasks",
      activeSummaryKey: "",
      activeFilter: null,
      taskId: new URLSearchParams(window.location.search).get("task_id") || "",
      orderId: new URLSearchParams(window.location.search).get("order_id") || "",
      selectedTaskId: "",
      orderTasks: [],
      summary: {
        order_count: 0,
        task_count: 0,
        running_task_count: 0,
        exception_count: 0,
        low_inventory_count: 0,
        overdue_risk_count: 0,
      },
      datasets: {
        orders: [],
        molds: [],
        equipment: [],
        tasks: [],
        injection: [],
        quality: [],
        inventory: [],
        multimodal: [],
      },
      tabs,
      multimodalCategories,
      quickQuestions,
      llmBadge: "工具调用",
      agentQuestion: "",
      agentContext: {},
      agentMessages: [],
      loadingAgentText: "",
      importType: "orders",
      importMessage: "",
      multimodalCategory: "document",
      multimodalDescription: "",
      multimodalMessage: "",
      multimodalPreviewUrl: "",
      multimodalFileName: "",
      lastMultimodalResult: null,
      task: null,
      reports: [],
      operatorName: "",
      reportAction: "加工完成",
      reportRemark: "",
      reportMessage: "",
      reportError: false,
      taskMessage: "正在读取任务...",
      qrDialog: {
        visible: false,
        imageUrl: "",
        title: "",
        url: "",
        message: "",
      },
    };
  },
  computed: {
    summaryItems() {
      return [
        { key: "orders", label: "订单数", value: this.summary.order_count, tab: "orders", hint: "查看订单明细" },
        { key: "tasks", label: "工序任务", value: this.summary.task_count, tab: "tasks", hint: "查看全部任务" },
        { key: "running", label: "加工中", value: this.summary.running_task_count, tab: "tasks", filter: "running", hint: "查看加工中任务" },
        { key: "quality", label: "质检异常", value: this.summary.exception_count, tab: "quality", hint: "查看异常记录" },
        { key: "lowInventory", label: "低库存", value: this.summary.low_inventory_count, tab: "inventory", filter: "lowInventory", hint: "查看低库存物料" },
        { key: "overdue", label: "延期风险", value: this.summary.overdue_risk_count, tab: "tasks", filter: "overdue", hint: "查看延期任务" },
      ];
    },
    activeTableName() {
      if (this.activeFilter === "running") return "加工中任务";
      if (this.activeFilter === "lowInventory") return "低库存物料";
      if (this.activeFilter === "overdue") return "延期风险任务";
      return tableNames[this.activeTab];
    },
    activeRows() {
      const rows = this.datasets[this.activeTab] || [];
      if (this.activeFilter === "running") {
        return rows.filter((row) => row.current_status === "加工中");
      }
      if (this.activeFilter === "lowInventory") {
        return rows.filter((row) => Number(row.qty) < Number(row.safety_qty));
      }
      if (this.activeFilter === "overdue") {
        const now = new Date();
        return rows.filter((row) => {
          if (row.current_status === "已完成" || !row.planned_end_at) return false;
          return new Date(row.planned_end_at.replace(" ", "T")) < now;
        });
      }
      return rows;
    },
    visibleAgentMessages() {
      const messages = [...this.agentMessages];
      if (this.loadingAgentText) {
        const insertIndex = messages[0]?.role === "user" ? 1 : 0;
        messages.splice(insertIndex, 0, { role: "assistant", content: this.loadingAgentText });
      }
      return messages;
    },
  },
  async mounted() {
    if (this.isReportPage) {
      if (this.orderId) {
        await this.loadOrderTasks();
        return;
      }
      this.taskId = this.taskId || "10086";
      await this.loadReportTask();
      return;
    }
    await this.refreshAll();
  },
  methods: {
    async request(path, options = {}) {
      return apiRequest(path, options);
    },
    async refreshAll() {
      const [summary, orders, molds, equipment, tasks, injection, quality, inventory, multimodal] = await Promise.all([
        this.request("/api/dashboard"),
        this.request("/api/orders"),
        this.request("/api/molds"),
        this.request("/api/equipment"),
        this.request("/api/tasks"),
        this.request("/api/injection-runs"),
        this.request("/api/quality-issues"),
        this.request("/api/inventory"),
        this.request("/api/multimodal-records"),
      ]);
      this.summary = summary;
      this.datasets = { orders, molds, equipment, tasks, injection, quality, inventory, multimodal };
    },
    async askCurrentQuestion() {
      const question = this.agentQuestion;
      this.agentQuestion = "";
      await this.askAgent(question);
    },
    async askQuickQuestion(question) {
      this.agentQuestion = question;
      await this.askAgent(question);
      this.agentQuestion = "";
    },
    openSummary(item) {
      this.activeTab = item.tab;
      this.activeFilter = item.filter || null;
      this.activeSummaryKey = item.key;
      this.$nextTick(() => {
        this.$refs.dataPanel?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    },
    selectTab(tab) {
      this.activeTab = tab;
      this.activeFilter = null;
      this.activeSummaryKey = "";
    },
    async openOrderQr(row) {
      const url = this.absoluteReportUrl(row.report_url || this.orderReportUrl(row.id));
      this.qrDialog = {
        visible: true,
        imageUrl: "",
        title: `${row.order_no} · ${row.product_name}`,
        url,
        message: "二维码生成中...",
      };
      try {
        const imageUrl = await QRCode.toDataURL(url, {
          errorCorrectionLevel: "M",
          margin: 2,
          width: 220,
          color: {
            dark: "#1f2933",
            light: "#ffffff",
          },
        });
        this.qrDialog.imageUrl = imageUrl;
        this.qrDialog.message = "";
      } catch (error) {
        this.qrDialog.message = error.message || "二维码生成失败。";
      }
    },
    closeReportQr() {
      this.qrDialog = {
        visible: false,
        imageUrl: "",
        title: "",
        url: "",
        message: "",
      };
    },
    absoluteReportUrl(url) {
      try {
        return new URL(url, window.location.origin).toString();
      } catch {
        return `${window.location.origin}/work-report`;
      }
    },
    orderReportUrl(orderId) {
      return orderId ? `/work-report?order_id=${encodeURIComponent(orderId)}` : "#";
    },
    async askAgent(question) {
      if (!question.trim()) {
        this.agentMessages.unshift({ role: "assistant", content: "请输入问题。" });
        return;
      }
      this.agentMessages.unshift({ role: "user", content: question });
      this.loadingAgentText = "正在调用工具查询...";
      try {
        const result = await this.request("/api/agent/ask", {
          method: "POST",
          body: JSON.stringify({ question, context: this.agentContext }),
        });
        this.agentContext = result.context || this.agentContext || {};
        this.llmBadge = result.used_llm ? "大模型工具调用" : "规则工具调用";
        this.agentMessages.splice(1, 0, { role: "assistant", content: `调用工具：${result.tool}\n${result.answer}` });
      } catch (error) {
        this.agentMessages.splice(1, 0, { role: "assistant", content: error.message });
      } finally {
        this.loadingAgentText = "";
      }
    },
    async importFile() {
      const file = this.$refs.importFileInput.files[0];
      if (!file) {
        this.importMessage = "请选择 .xlsx 或 .csv 文件。";
        return;
      }
      const form = new FormData();
      form.append("file", file);
      this.importMessage = "正在导入...";
      try {
        const result = await this.request(`/api/import/${this.importType}`, { method: "POST", body: form });
        this.importMessage = `导入完成：总 ${result.total_rows} 行，成功 ${result.success_rows} 行，失败 ${result.error_rows} 行。`;
        this.$refs.importFileInput.value = "";
        await this.refreshAll();
      } catch (error) {
        this.importMessage = error.message;
      }
    },
    selectMultimodalFile() {
      const file = this.$refs.multimodalFileInput.files[0];
      if (this.multimodalPreviewUrl) {
        URL.revokeObjectURL(this.multimodalPreviewUrl);
      }
      if (!file) {
        this.multimodalPreviewUrl = "";
        this.multimodalFileName = "";
        return;
      }
      this.multimodalFileName = file.name;
      this.multimodalPreviewUrl = URL.createObjectURL(file);
      this.multimodalMessage = "";
      this.lastMultimodalResult = null;
    },
    clearMultimodalFile() {
      if (this.multimodalPreviewUrl) {
        URL.revokeObjectURL(this.multimodalPreviewUrl);
      }
      this.multimodalPreviewUrl = "";
      this.multimodalFileName = "";
      this.lastMultimodalResult = null;
      this.$refs.multimodalFileInput.value = "";
    },
    async uploadMultimodal() {
      const file = this.$refs.multimodalFileInput.files[0];
      if (!file) {
        this.multimodalMessage = "请先拍照或选择要识别的图片。";
        return;
      }
      const form = new FormData();
      form.append("category", this.multimodalCategory);
      form.append("description", this.multimodalDescription.trim());
      form.append("file", file);
      this.multimodalMessage = "正在上传并识别...";
      try {
        const result = await this.request("/api/multimodal/upload", { method: "POST", body: form });
        this.multimodalMessage = "识别完成，结果如下。";
        this.lastMultimodalResult = result;
        this.multimodalDescription = "";
        this.clearMultimodalFile();
        this.lastMultimodalResult = result;
        await this.refreshAll();
        this.$nextTick(() => {
          this.$refs.recognitionResult?.scrollIntoView({ behavior: "smooth", block: "center" });
        });
      } catch (error) {
        this.multimodalMessage = error.message;
      }
    },
    categoryName(category) {
      const item = this.multimodalCategories.find((option) => option.key === category);
      return item ? item.label : category;
    },
    extractedText(extracted) {
      return Object.entries(extracted || {})
        .filter(([, value]) => value)
        .map(([key, value]) => `${key}：${value}`)
        .join("，") || "暂无结构化字段";
    },
    extractedEntries(extracted) {
      return Object.entries(extracted || {}).filter(([, value]) => value);
    },
    async loadReportTask() {
      if (this.orderId) {
        this.taskId = this.selectedTaskId;
      }
      if (!this.taskId) {
        this.task = null;
        this.reports = [];
        this.taskMessage = "请选择要报工的工序。";
        return;
      }
      this.taskMessage = "正在读取任务...";
      try {
        const result = await this.request(`/api/tasks/${encodeURIComponent(this.taskId)}`);
        this.task = result.task;
        this.reports = result.reports || [];
        this.operatorName = this.operatorName || this.task.owner_name;
        this.reportError = false;
      } catch (error) {
        this.task = null;
        this.reports = [];
        this.taskMessage = error.message;
      }
    },
    async loadOrderTasks() {
      this.taskMessage = "正在读取订单工序...";
      try {
        const tasks = await this.request(`/api/tasks?order_id=${encodeURIComponent(this.orderId)}`);
        this.orderTasks = tasks;
        if (!tasks.length) {
          this.task = null;
          this.reports = [];
          this.taskMessage = "该订单暂无工序任务。";
          return;
        }
        const activeTask = tasks.find((item) => item.current_status !== "已完成") || tasks[0];
        this.selectedTaskId = activeTask.id;
        this.taskId = activeTask.id;
        await this.loadReportTask();
      } catch (error) {
        this.task = null;
        this.reports = [];
        this.taskMessage = error.message;
      }
    },
    async submitReport() {
      this.reportError = false;
      this.reportMessage = "正在提交...";
      try {
        await this.request(`/api/tasks/${encodeURIComponent(this.taskId)}/reports`, {
          method: "POST",
          body: JSON.stringify({
            action: this.reportAction,
            operator_name: this.operatorName.trim() || (this.task ? this.task.owner_name : ""),
            remark: this.reportRemark.trim(),
          }),
        });
        this.reportMessage = "报工已提交，任务状态已更新。";
        this.reportRemark = "";
        await this.loadReportTask();
        if (this.orderId) {
          await this.loadOrderTasks();
        }
      } catch (error) {
        this.reportError = true;
        this.reportMessage = error.message;
      }
    },
  },
};
</script>
