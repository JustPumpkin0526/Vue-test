<template>
  <div class="space-y-4">
    <div class="flex items-center gap-3">
      <input v-model="q" placeholder="동영상명으로 검색" class="w-80 border rounded-md px-3 py-2" />
      <select v-model="filter" class="border rounded-md px-3 py-2">
        <option value="">필터 없음</option>
        <option value="recent">최근 업로드</option>
        <option value="large">대용량</option>
      </select>
      <button class="px-4 py-2 rounded-md bg-vix-primary text-white" @click="search">검색</button>
    </div>

    <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="v in items" :key="v.id" class="border rounded-xl p-3 bg-gray-50">
        <div class="aspect-video bg-gray-200 mb-2 rounded-md flex items-center justify-center text-gray-500 overflow-hidden">
          <video v-if="v.url" :src="v.url" class="w-full h-full object-cover rounded-md" />
          <span v-else>썸네일</span>
        </div>
        <div class="font-semibold">{{ v.title }}</div>
        <div class="text-xs text-gray-500">업로드: {{ v.date }}</div>

        <div class="mt-2 flex gap-2">
          <button class="px-3 py-1 rounded bg-gray-100" @click="openItem(v)">열기</button>
          <button class="px-3 py-1 rounded bg-gray-100" @click="rerun(v)">추가 추론</button>
          <button class="px-3 py-1 rounded bg-gray-100" @click="remove(v)">삭제</button>
        </div>
      </div>
    </div>

    <Pagination :page="page" :pages="pages" @update:page="(p)=>{page=p; search();}" />
  </div>
</template>

<script setup>
import { ref } from "vue";
import Pagination from "@/components/Pagination.vue";
import api from "@/services/api";

const q = ref("");
const filter = ref("");
const items = ref([]);
const page = ref(1);
const pages = ref(0);

function search() {
  // localStorage에서 저장된 동영상 리스트 불러오기
  const saved = JSON.parse(localStorage.getItem('vss_videos') || '[]');
  items.value = saved;
  pages.value = 1;
}
search();

function openItem(v) {
  // 실제 구현 필요
}
function rerun(v) {
  // 실제 구현 필요
}
function remove(v) {
  const saved = JSON.parse(localStorage.getItem('vss_videos') || '[]');
  const filtered = saved.filter(item => item.id !== v.id);
  localStorage.setItem('vss_videos', JSON.stringify(filtered));
  search();
}
</script>
