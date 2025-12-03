<template>
  <div class="grid lg:grid-cols-[1fr_1200px] gap-6 h-[calc(100vh-120px)] p-10">
    <section class="rounded-2xl border border-black p-4">
      <h2 class="font-semibold mb-3">현재 리포트</h2>

      <div class="h-[calc(100vh-240px)] border border-black rounded-xl p-3 bg-gray-50 overflow-auto whitespace-pre-wrap text-sm">
        {{ report }}
      </div>

      <div class="mt-3 flex gap-2">
        <button class="px-3 py-2 rounded-md bg-gray-100" @click="prevPage">이전 페이지</button>
        <button class="px-3 py-2 rounded-md bg-gray-100" @click="nextPage">다음 페이지</button>
        <button class="px-3 py-2 rounded-md bg-vix-primary text-white" @click="exportFile">리포트 내보내기</button>
      </div>
    </section>

    <aside class="rounded-2xl border border-black p-4 w-[1200px] flex flex-col justify-between">
      <div>
        <h3 class="font-semibold mb-3">리포트 리스트</h3>
        <ul class="space-y-2">
          <li v-for="r in list" :key="r.id" class="p-2 border border-black rounded-md flex items-center justify-between">
            <span class="text-sm">{{ r.title }}</span>
            <button class="px-2 py-1 bg-gray-100 rounded" @click="open(r)">열기</button>
          </li>
        </ul>
      </div>

      <div class="mt-4">
        <Pagination :page="page" :pages="pages" @update:page="(p)=>{page=p; loadList();}" />
      </div>
    </aside>
  </div>
</template>

<script setup>
import { ref } from "vue";
import Pagination from "@/components/Pagination.vue";
import api from "@/services/api";

const report = ref("");
const list = ref([]);
const page = ref(1);
const pages = ref(0);

function loadList() {
  // 실제 API 연동 시 아래 주석 해제
  // const res = api.listReports({ page: page.value });
  // list.value = res.items;
  // pages.value = res.pages;
  list.value = [];
  pages.value = 0;
}
loadList();

function open(r) {
  report.value = r.content || "";
}
function prevPage() { /* 실제 구현 필요 */ }
function nextPage() { /* 실제 구현 필요 */ }
function exportFile() { /* 실제 구현 필요 */ }
</script>
