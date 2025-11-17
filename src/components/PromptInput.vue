<template>
  <div class="flex items-center gap-2">
    <input
      v-model="model"
      :placeholder="placeholder"
      class="w-full rounded-xl border-[1px] border-black px-4 py-3 bg-white"
      @keyup.enter="emitAsk" />
    <button
      class="rounded-lg bg-vix-primary text-white px-4 py-2"
      @click="emitAsk">
      Ask
    </button>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  modelValue: { type: String, default: "" },
  placeholder: { type: String, default: "프롬프트 입력..." }
});
const emit = defineEmits(["update:modelValue", "ask"]);
const model = computed({
  get: () => props.modelValue,
  set: (v) => emit("update:modelValue", v)
});
const emitAsk = () => emit("ask", model.value);
</script>
