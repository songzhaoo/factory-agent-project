export const tableNames = {
  tasks: "工序任务",
  orders: "订单",
  molds: "模具",
  equipment: "设备排产",
  injection: "注塑生产",
  quality: "质检异常",
  inventory: "库存管理",
  multimodal: "多模态识别记录",
};

export const tabs = [
  { key: "tasks", label: "工序任务" },
  { key: "orders", label: "订单" },
  { key: "molds", label: "模具" },
  { key: "equipment", label: "设备排产" },
  { key: "injection", label: "注塑" },
  { key: "quality", label: "质检" },
  { key: "inventory", label: "库存" },
  { key: "multimodal", label: "多模态" },
];

export const multimodalCategories = [
  { key: "document", label: "单据识别" },
  { key: "quality", label: "质检图片分析" },
  { key: "equipment", label: "设备现场识别" },
  { key: "inventory", label: "库存标签盘点" },
  { key: "drawing", label: "图纸/工艺单理解" },
];

export const quickQuestions = [
  { text: "CNC 做完了吗", value: "洗衣机面板模具 CNC 做完了吗" },
  { text: "模具工序进度", value: "深孔钻、车床、铣床、磨床这些工序现在进度怎么样" },
  { text: "注塑生产", value: "注塑机现在生产什么" },
  { text: "延期风险", value: "哪些任务有延期风险" },
  { text: "库存够不够", value: "ABS 和 PP 库存够不够" },
  { text: "质检异常", value: "今天有哪些质检异常" },
  { text: "图片识别记录", value: "最近上传的图片识别记录有哪些" },
];
