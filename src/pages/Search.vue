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
        <div class="aspect-video bg-gray-200 mb-2 rounded-md flex items-center justify-center text-gray-500">
          썸네일
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

async function search() {
  // 실제 API 연동 시 아래 주석 해제
  // const res = await api.searchVideos({ q: q.value, filter: filter.value, page: page.value });
  // items.value = res.items;
  // pages.value = res.pages;
  items.value = [];
  pages.value = 0;
}
search();

function openItem(v) {
  // 실제 구현 필요
}
function rerun(v) {
  // 실제 구현 필요
}
function remove(v) {
  // 실제 구현 필요
}
</script>
