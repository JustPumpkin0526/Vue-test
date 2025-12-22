<template>
  <div class="w-full h-full bg-gradient-to-br from-gray-200 to-gray-300 via-gray-100 dark:from-gray-950 dark:to-gray-900 dark:via-gray-950 p-10">
    <div class="grid lg:grid-cols-[1fr_400px] gap-6 h-full">
      <!-- 좌측: 리포트 뷰어 -->
      <section
        class="rounded-2xl p-6 bg-gradient-to-br from-white via-gray-50 to-gray-100 dark:from-gray-950 dark:via-gray-950 dark:to-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm hover:shadow-md transition-shadow duration-300 flex flex-col">
        <!-- 헤더 -->
        <header class="flex items-center justify-between px-1 pb-4 mb-4 border-b border-slate-800/70 dark:border-gray-200/30">
          <div class="flex flex-col gap-1">
            <div
              class="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 dark:bg-emerald-500/20 border border-emerald-400/40 dark:border-emerald-400/60 w-fit">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span class="text-[11px] font-semibold tracking-wide text-emerald-600 dark:text-emerald-400 uppercase">
                {{ tReport.reportViewer }}
              </span>
            </div>
            <p class="text-xs md:text-sm text-black dark:text-gray-200 mt-1">
              {{ selectedReport?.title || tReport.selectReport }}
              <span v-if="selectedReport?.createdAt" class="text-gray-500 dark:text-gray-400 ml-2">
                · {{ formatDate(selectedReport.createdAt) }}
              </span>
            </p>
          </div>
          <div class="flex items-center gap-2">
            <button
              v-if="selectedReport"
              @click="prevPage"
              :disabled="currentPage <= 1"
              class="w-9 h-9 flex items-center justify-center bg-slate-200/70 dark:bg-gray-700 hover:bg-slate-400/80 dark:hover:bg-gray-600 border border-slate-500/60 dark:border-gray-600 text-slate-700 dark:text-gray-200 rounded-lg shadow transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
              :title="tReport.prevPage">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <button
              v-if="selectedReport"
              @click="nextPage"
              :disabled="currentPage >= totalPages"
              class="w-9 h-9 flex items-center justify-center bg-slate-200/70 dark:bg-gray-700 hover:bg-slate-400/80 dark:hover:bg-gray-600 border border-slate-500/60 dark:border-gray-600 text-slate-700 dark:text-gray-200 rounded-lg shadow transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
              :title="tReport.nextPage">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
            <button
              v-if="selectedReport"
              @click="exportFile"
              class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500/90 dark:bg-emerald-600 hover:bg-emerald-400 dark:hover:bg-emerald-500 text-white shadow-lg shadow-emerald-500/30 dark:shadow-emerald-600/30 transition-all duration-200 transform hover:scale-[1.03] active:scale-[0.97]">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span class="text-sm font-medium">{{ tReport.export }}</span>
            </button>
          </div>
        </header>

        <!-- 리포트 내용 -->
        <div
          v-if="selectedReport"
          class="flex-1 border border-gray-200 dark:border-gray-800 rounded-xl p-6 bg-white dark:bg-gray-900 overflow-auto shadow-inner">
          <div class="prose prose-sm max-w-none dark:prose-invert">
            <div class="whitespace-pre-wrap text-sm leading-relaxed text-gray-800 dark:text-gray-200" v-html="formattedReport"></div>
          </div>
        </div>

        <!-- 빈 상태 -->
        <div v-else class="flex-1 flex items-center justify-center border border-gray-200 dark:border-gray-800 rounded-xl bg-gray-50 dark:bg-gray-900">
          <div class="text-center">
            <svg class="w-16 h-16 mx-auto text-gray-400 dark:text-gray-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p class="text-gray-500 dark:text-gray-400 text-sm">{{ tReport.selectToView }}</p>
          </div>
        </div>

        <!-- 페이지 정보 -->
        <div v-if="selectedReport" class="mt-4 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>{{ tReport.page }} {{ currentPage }} / {{ totalPages }}</span>
          <span>{{ selectedReport.wordCount || 0 }} {{ tReport.words }}</span>
        </div>
      </section>

      <!-- 우측: 리포트 리스트 -->
      <aside
        class="rounded-2xl p-6 bg-gradient-to-br from-white via-gray-50 to-gray-100 dark:from-gray-950 dark:via-gray-950 dark:to-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm hover:shadow-md transition-shadow duration-300 flex flex-col">
        <!-- 헤더 -->
        <header class="flex items-center justify-between px-1 pb-4 mb-4 border-b border-slate-800/70 dark:border-gray-200/30">
          <div class="flex flex-col gap-1">
            <div
              class="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-blue-500/10 dark:bg-blue-500/20 border border-blue-400/40 dark:border-blue-400/60 w-fit">
              <span class="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse"></span>
              <span class="text-[11px] font-semibold tracking-wide text-blue-600 dark:text-blue-400 uppercase">
                {{ tReport.reportLibrary }}
              </span>
            </div>
            <p class="text-xs text-black dark:text-gray-200 mt-1">{{ tReport.total }} {{ totalReports }} {{ tReport.totalReports }}</p>
          </div>
        </header>

        <!-- 검색 및 필터 -->
        <div class="mb-4 space-y-2">
          <div class="relative">
            <input
              v-model="searchQuery"
              type="text"
              :placeholder="tReport.searchPlaceholder"
              class="w-full rounded-xl border border-slate-300 dark:border-gray-600 focus:border-emerald-500 dark:focus:border-emerald-400 focus:ring-2 focus:ring-emerald-300 dark:focus:ring-emerald-500 px-4 py-2.5 pl-10 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 text-sm transition-all"
              @input="handleSearch" />
            <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" fill="none"
              stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <div class="flex gap-2">
            <button
              @click="sortBy = 'date'"
              :class="[
                'px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
                sortBy === 'date'
                  ? 'bg-emerald-500 dark:bg-emerald-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600'
              ]">
              {{ tReport.sortByDate }}
            </button>
            <button
              @click="sortBy = 'title'"
              :class="[
                'px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
                sortBy === 'title'
                  ? 'bg-emerald-500 dark:bg-emerald-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600'
              ]">
              {{ tReport.sortByTitle }}
            </button>
          </div>
        </div>

        <!-- 리포트 리스트 -->
        <div class="flex-1 overflow-y-auto space-y-3">
          <div v-if="filteredList.length === 0" class="text-center py-12">
            <svg class="w-12 h-12 mx-auto text-gray-400 dark:text-gray-500 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p class="text-gray-500 dark:text-gray-400 text-sm">{{ tReport.noReports }}</p>
          </div>

          <div
            v-for="r in filteredList"
            :key="r.id"
            @click="open(r)"
            :class="[
              'group p-4 border rounded-xl cursor-pointer transition-all duration-200',
              selectedReport?.id === r.id
                ? 'bg-emerald-50 dark:bg-emerald-900/30 border-emerald-300 dark:border-emerald-600 shadow-md'
                : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:border-emerald-300 dark:hover:border-emerald-600 hover:shadow-md'
            ]">
            <div class="flex items-start justify-between gap-3">
              <div class="flex-1 min-w-0">
                <h4 class="font-semibold text-sm text-gray-900 dark:text-gray-100 mb-1 truncate group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                  {{ r.title || tReport.noTitle }}
                </h4>
                <p v-if="r.description" class="text-xs text-gray-600 dark:text-gray-400 line-clamp-2 mb-2">
                  {{ r.description }}
                </p>
                <div class="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                  <span v-if="r.createdAt" class="flex items-center gap-1">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    {{ formatDate(r.createdAt) }}
                  </span>
                  <span v-if="r.wordCount" class="flex items-center gap-1">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    {{ r.wordCount }} {{ tReport.words }}
                  </span>
                </div>
              </div>
              <button
                @click.stop="open(r)"
                class="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-emerald-500/10 dark:bg-emerald-500/20 hover:bg-emerald-500/20 dark:hover:bg-emerald-500/30 text-emerald-600 dark:text-emerald-400 rounded-lg transition-all opacity-0 group-hover:opacity-100">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- 페이지네이션 -->
        <div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div class="flex items-center justify-center gap-2">
            <button 
              class="px-3 py-1 rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all" 
              :disabled="page <= 1" 
              @click="handlePageChange(page - 1)">
              〈
            </button>
            <span class="text-sm text-gray-600 dark:text-gray-400">Page {{ page }} / {{ pages }}</span>
            <button 
              class="px-3 py-1 rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all" 
              :disabled="page >= pages" 
              @click="handlePageChange(page + 1)">
              〉
            </button>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import api from "@/services/api";
import { marked } from 'marked';
import { useSettingStore } from '@/stores/settingStore';

const settingStore = useSettingStore();

// ==================== 다국어 지원 ====================
const reportTranslations = {
  ko: {
    reportViewer: "Report Viewer",
    selectReport: "리포트를 선택하세요",
    prevPage: "이전 페이지",
    nextPage: "다음 페이지",
    export: "내보내기",
    reportLibrary: "Report Library",
    total: "총",
    totalReports: "개의 리포트",
    searchPlaceholder: "리포트 검색...",
    sortByDate: "최신순",
    sortByTitle: "제목순",
    noReports: "리포트가 없습니다",
    noTitle: "제목 없음",
    selectToView: "리포트를 선택하여 내용을 확인하세요",
    page: "페이지",
    word: "단어",
    words: "단어"
  },
  en: {
    reportViewer: "Report Viewer",
    selectReport: "Select a report",
    prevPage: "Previous Page",
    nextPage: "Next Page",
    export: "Export",
    reportLibrary: "Report Library",
    total: "Total",
    totalReports: "reports",
    searchPlaceholder: "Search reports...",
    sortByDate: "Latest",
    sortByTitle: "Title",
    noReports: "No reports",
    noTitle: "No Title",
    selectToView: "Select a report to view its content",
    page: "Page",
    word: "word",
    words: "words"
  }
};

const tReport = computed(() => reportTranslations[settingStore.language] || reportTranslations.ko);

const report = ref("");
const selectedReport = ref(null);
const list = ref([]);
const page = ref(1);
const pages = ref(0);
const searchQuery = ref("");
const sortBy = ref("date");
const currentPage = ref(1);
const totalPages = ref(1);

// 필터링 및 정렬된 리스트
const filteredList = computed(() => {
  let filtered = [...list.value];

  // 검색 필터
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase();
    filtered = filtered.filter(r =>
      (r.title || '').toLowerCase().includes(query) ||
      (r.description || '').toLowerCase().includes(query) ||
      (r.content || '').toLowerCase().includes(query)
    );
  }

  // 정렬
  if (sortBy.value === 'date') {
    filtered.sort((a, b) => {
      const dateA = new Date(a.createdAt || 0);
      const dateB = new Date(b.createdAt || 0);
      return dateB - dateA; // 최신순
    });
  } else if (sortBy.value === 'title') {
    filtered.sort((a, b) => {
      const titleA = (a.title || '').toLowerCase();
      const titleB = (b.title || '').toLowerCase();
      return titleA.localeCompare(titleB);
    });
  }

  return filtered;
});

// 총 리포트 수
const totalReports = computed(() => list.value.length);

// 포맷된 리포트 내용 (Markdown 지원)
const formattedReport = computed(() => {
  if (!report.value) return "";
  try {
    return marked.parse(report.value);
  } catch (e) {
    return report.value;
  }
});

function loadList() {
  // 실제 API 연동 시 아래 주석 해제
  // const res = api.listReports({ page: page.value });
  // list.value = res.items;
  // pages.value = res.pages;
  
  // 임시 더미 데이터 (개발용)
  list.value = [
    {
      id: 1,
      title: "2024년 1분기 보안 리포트",
      description: "1분기 동안 발생한 보안 사고 및 대응 현황을 정리한 리포트입니다.",
      content: "# 2024년 1분기 보안 리포트\n\n## 개요\n\n2024년 1분기 동안 총 15건의 보안 사고가 발생했습니다.\n\n## 주요 사항\n\n- 네트워크 침입 시도: 8건\n- 악성 코드 감지: 5건\n- 데이터 유출 시도: 2건\n\n## 대응 조치\n\n모든 사고에 대해 즉시 대응 조치를 취했으며, 추가 보안 강화 방안을 수립했습니다.",
      createdAt: "2024-03-31T10:00:00Z",
      wordCount: 250
    },
    {
      id: 2,
      title: "월간 활동 보고서 - 3월",
      description: "3월 한 달간의 주요 활동 및 성과를 정리한 리포트입니다.",
      content: "# 월간 활동 보고서 - 3월\n\n## 주요 성과\n\n- 신규 프로젝트 3건 완료\n- 고객 만족도 95% 달성\n- 팀 회의 12회 진행\n\n## 향후 계획\n\n4월에는 더욱 적극적인 활동을 계획하고 있습니다.",
      createdAt: "2024-03-30T14:30:00Z",
      wordCount: 180
    }
  ];
  pages.value = 1;
}
loadList();

function open(r) {
  selectedReport.value = r;
  report.value = r.content || "";
  currentPage.value = 1;
  // 리포트 내용을 페이지로 나누는 로직 (간단한 구현)
  const words = (r.content || '').split(/\s+/);
  totalPages.value = Math.max(1, Math.ceil(words.length / 500)); // 페이지당 500단어
}

function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--;
    scrollToTop();
  }
}

function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++;
    scrollToTop();
  }
}

function scrollToTop() {
  const viewer = document.querySelector('.overflow-auto');
  if (viewer) {
    viewer.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

function exportFile() {
  if (!selectedReport.value) return;
  
  // 리포트를 텍스트 파일로 내보내기
  const content = selectedReport.value.content || report.value;
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${selectedReport.value.title || 'report'}.txt`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function handleSearch() {
  // 검색은 computed property에서 자동 처리됨
}

function handlePageChange(newPage) {
  if (newPage >= 1 && newPage <= pages.value) {
    page.value = newPage;
    loadList();
  }
}

function formatDate(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  const locale = settingStore.language === 'ko' ? 'ko-KR' : 'en-US';
  return date.toLocaleDateString(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

// 정렬 변경 시 자동 업데이트
watch(sortBy, () => {
  // computed property가 자동으로 업데이트됨
});
</script>
