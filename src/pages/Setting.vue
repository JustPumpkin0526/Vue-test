<template>
  <div class="grid lg:grid-cols-2 gap-6">
    <section class="rounded-2xl border p-4">
      <h2 class="font-semibold mb-3">Chunk 설정</h2>
      <label class="block text-sm mb-1">Chunk Size (sec)</label>
      <input v-model.number="chunk" type="number" min="1" class="border rounded-md px-3 py-2 w-48" />
      <p class="text-xs text-gray-500 mt-2">동영상 추론에서 분할 단위를 설정합니다.</p>
    </section>

    <section class="rounded-2xl border p-4">
      <h2 class="font-semibold mb-3">Caption Summarization Prompt</h2>
      <textarea v-model="captionPrompt" rows="6" class="w-full border rounded-md p-3"></textarea>
    </section>

    <section class="rounded-2xl border p-4">
      <h2 class="font-semibold mb-3">Summary Aggregation Prompt</h2>
      <textarea v-model="aggregationPrompt" rows="6" class="w-full border rounded-md p-3"></textarea>
    </section>

    <section class="rounded-2xl border p-4">
      <h2 class="font-semibold mb-3">기타 파라미터</h2>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-sm mb-1">Top-k</label>
          <input v-model.number="topk" type="number" min="1" class="border rounded-md px-3 py-2 w-32" />
        </div>
        <div>
          <label class="block text-sm mb-1">Temperature</label>
          <input v-model.number="temp" type="number" step="0.1" min="0" class="border rounded-md px-3 py-2 w-32" />
        </div>
      </div>

      <div class="mt-4">
        <button class="px-4 py-2 rounded-md bg-vix-primary text-white" @click="save">저장</button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from "vue";
import api from "@/services/api";

const chunk = ref(60);
const captionPrompt = ref("You will be given captions from sequential clips of a video...");
const aggregationPrompt = ref("Aggregate captions into coherent scenes ...");
const topk = ref(5);
const temp = ref(0.2);

function save() {
  api.saveSetting({
    chunk: chunk.value,
    captionPrompt: captionPrompt.value,
    aggregationPrompt: aggregationPrompt.value,
    topk: topk.value,
    temp: temp.value
  });
  alert("설정을 저장했습니다.");
}
</script>
