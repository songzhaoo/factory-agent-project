<template>
  <section class="summary-grid">
    <article
      v-for="item in items"
      :key="item.label"
      class="summary-card"
      :class="{ active: activeKey === item.key }"
      @click="$emit('open', item)"
    >
      <span>{{ item.label }}</span>
      <strong>{{ item.value }}</strong>
      <small>{{ item.hint }}</small>
    </article>
  </section>
</template>

<script>
export default {
  name: "SummaryGrid",
  props: {
    items: {
      type: Array,
      required: true,
    },
    activeKey: {
      type: String,
      default: "",
    },
  },
  emits: ["open"],
};
</script>
