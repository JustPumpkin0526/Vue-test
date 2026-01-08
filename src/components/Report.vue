<template>
  <div class="w-full min-h-screen bg-gradient-to-br from-gray-200 to-gray-300 via-gray-100 dark:from-gray-950 dark:to-gray-900 dark:via-gray-950 p-10">
    <div class="grid lg:grid-cols-[1fr_400px] gap-6 h-full">
      <!-- 좌측: 리포트 뷰어 -->
      <section
        ref="viewerSectionRef"
        class="h-[calc(100vh-10rem)] rounded-2xl p-6 bg-gradient-to-br from-white via-gray-50 to-gray-100 dark:from-gray-950 dark:via-gray-950 dark:to-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm hover:shadow-md transition-shadow duration-300 flex flex-col relative"
        >
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
          class="flex-1 border border-gray-200 dark:border-gray-800 rounded-xl p-6 bg-white dark:bg-gray-900 overflow-hidden shadow-inner"
          :style="{ maxHeight: '100%', overflowY: 'auto' }">
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

        <!-- Resize 핸들 (하단) -->
        <div
          v-if="selectedReport"
          class="absolute bottom-0 left-0 right-0 h-2 cursor-ns-resize hover:bg-emerald-500/20 dark:hover:bg-emerald-500/30 transition-colors group"
          @mousedown="startResize"
          :title="tReport.resizeHint">
          <div class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-12 h-0.5 bg-emerald-500/50 dark:bg-emerald-400/50 rounded-full group-hover:bg-emerald-500 dark:group-hover:bg-emerald-400 transition-colors"></div>
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
              'group p-4 border rounded-xl cursor-pointer transition-all duration-200 relative',
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
              <div class="flex items-center gap-1">
                <button
                  @click.stop="open(r)"
                  class="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-emerald-500/10 dark:bg-emerald-500/20 hover:bg-emerald-500/20 dark:hover:bg-emerald-500/30 text-emerald-600 dark:text-emerald-400 rounded-lg transition-all opacity-0 group-hover:opacity-100">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                  </svg>
                </button>
                <!-- 햄버거 메뉴 버튼 -->
                <button
                  @click.stop="openContextMenu(r, $event)"
                  class="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300 rounded-lg transition-all opacity-0 group-hover:opacity-100">
                  <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <circle cx="12" cy="5" r="1.5" />
                    <circle cx="12" cy="12" r="1.5" />
                    <circle cx="12" cy="19" r="1.5" />
                  </svg>
                </button>
              </div>
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

    <!-- 컨텍스트 메뉴 (Teleport로 body에 렌더링) -->
    <Teleport to="body">
      <div v-if="contextMenu.visible" class="fixed z-[200]"
        :style="{ left: `${contextMenu.x}px`, top: `${contextMenu.y}px` }" @click.stop>
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-100 dark:border-gray-700 overflow-hidden w-[160px]">
          <button 
            class="w-full text-left px-4 py-3 text-red-600 dark:text-red-400 hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2 transition-colors"
            @click.stop="handleDeleteReport">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            <span>{{ tReport.delete }}</span>
          </button>
        </div>
      </div>
    </Teleport>

    <!-- 삭제 확인 다이얼로그 -->
    <Transition name="modal">
      <div v-if="showDeleteConfirm" class="fixed inset-0 flex items-center justify-center z-[100] bg-black/50 backdrop-blur-sm">
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-8 min-w-[350px] max-w-[90vw] relative transform transition-all duration-300">
          <div class="text-lg font-semibold mb-6 text-center text-gray-800 dark:text-gray-200">
            <p class="mb-2">{{ tReport.deleteConfirm }}</p>
            <p class="text-sm font-normal text-gray-600 dark:text-gray-400">{{ tReport.deleteConfirmDetail }}</p>
          </div>
          <div class="flex justify-end gap-3 mt-8">
            <button
              class="px-6 py-2.5 rounded-xl bg-red-600 dark:bg-red-700 text-white hover:bg-red-700 dark:hover:bg-red-600 transition-all duration-300 transform hover:scale-105 active:scale-95 font-medium shadow-sm"
              @click="confirmDeleteReport">{{ tReport.delete }}</button>
            <button
              class="px-6 py-2.5 rounded-xl bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600 transition-all duration-300 transform hover:scale-105 active:scale-95 font-medium shadow-sm"
              @click="showDeleteConfirm = false">{{ tReport.cancel }}</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from "vue";
import { marked } from 'marked';
import { useSettingStore } from '@/stores/settingStore';

const settingStore = useSettingStore();

// ==================== 상수 정의 ====================
const API_BASE_URL = 'http://localhost:8001';

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
    words: "단어",
    delete: "삭제",
    deleteConfirm: "이 보고서를 삭제하시겠습니까?",
    deleteConfirmDetail: "이 작업은 되돌릴 수 없습니다.",
    cancel: "취소",
    resizeHint: "드래그하여 높이 조절"
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
    words: "words",
    delete: "Delete",
    deleteConfirm: "Are you sure you want to delete this report?",
    deleteConfirmDetail: "This action cannot be undone.",
    cancel: "Cancel",
    resizeHint: "Drag to resize height"
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
const contextMenu = ref({ visible: false, x: 0, y: 0, report: null });
const showDeleteConfirm = ref(false);
const reportToDelete = ref(null);
const viewerSectionRef = ref(null);
const viewerHeight = ref(600); // 기본 높이
const isResizing = ref(false);
const resizeStartY = ref(0);
const resizeStartHeight = ref(0);

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

async function loadList() {
  const userId = localStorage.getItem("vss_user_id");
  
  try {
    // API에서 보고서 목록 로드 시도
    if (userId) {
      const response = await fetch(`${API_BASE_URL}/reports?user_id=${userId}&page=${page.value}`);
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.reports) {
          list.value = data.reports.map(r => ({
            id: r.id || r.report_id,
            title: r.title,
            description: r.description || '',
            content: r.content || r.report_content || '',
            createdAt: r.created_at || r.createdAt,
            wordCount: r.word_count || r.wordCount || 0
          }));
          pages.value = data.pages || Math.max(1, Math.ceil(list.value.length / 10));
          return;
        }
      }
    }
  } catch (error) {
    console.warn('보고서 API 로드 실패, localStorage에서 로드:', error);
  }
  
  // API 실패 시 localStorage에서 로드
  const reportsKey = `vss_reports_${userId || 'guest'}`;
  const storedReports = JSON.parse(localStorage.getItem(reportsKey) || '[]');
  
  // 페이지네이션 적용
  const itemsPerPage = 10;
  const startIndex = (page.value - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  
  list.value = storedReports.slice(startIndex, endIndex);
  pages.value = Math.max(1, Math.ceil(storedReports.length / itemsPerPage));
  
  // 보고서가 없으면 빈 배열
  if (storedReports.length === 0) {
    list.value = [];
    pages.value = 1;
  }
}
loadList();

async function open(r) {
  selectedReport.value = r;
  
  // 보고서 내용이 없으면 API에서 로드 시도
  if (!r.content) {
    const userId = localStorage.getItem("vss_user_id");
    if (userId && r.id) {
      try {
        const response = await fetch(`${API_BASE_URL}/reports/${r.id}?user_id=${userId}`);
        if (response.ok) {
          const data = await response.json();
          if (data.success && data.report) {
            r.content = data.report.content || data.report.report_content || '';
            r.wordCount = data.report.word_count || data.report.wordCount || 0;
          }
        }
      } catch (error) {
        console.warn('보고서 상세 로드 실패:', error);
      }
    }
  }
  
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

// ==================== 컨텍스트 메뉴 ====================
function openContextMenu(report, event) {
  event.stopPropagation();
  
  // 메뉴 위치 계산 (화면 경계 고려)
  const x = Math.min(event.clientX, window.innerWidth - 180);
  const y = Math.min(event.clientY, window.innerHeight - 100);
  
  contextMenu.value = {
    visible: true,
    x: x,
    y: y,
    report: report
  };
}

function closeContextMenu() {
  contextMenu.value.visible = false;
  contextMenu.value.report = null;
}

function handleDeleteReport() {
  if (!contextMenu.value.report) return;
  
  reportToDelete.value = contextMenu.value.report;
  closeContextMenu();
  showDeleteConfirm.value = true;
}

async function confirmDeleteReport() {
  if (!reportToDelete.value) return;
  
  const reportId = reportToDelete.value.id;
  const userId = localStorage.getItem("vss_user_id");
  
  try {
    // API에서 삭제 시도
    if (userId && reportId) {
      try {
        const response = await fetch(`${API_BASE_URL}/reports/${reportId}?user_id=${userId}`, {
          method: 'DELETE'
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.success) {
            // API 삭제 성공
            console.log('보고서 삭제 성공 (API)');
          }
        }
      } catch (error) {
        console.warn('보고서 API 삭제 실패, localStorage에서 삭제:', error);
      }
    }
    
    // localStorage에서 삭제
    const reportsKey = `vss_reports_${userId || 'guest'}`;
    const storedReports = JSON.parse(localStorage.getItem(reportsKey) || '[]');
    const updatedReports = storedReports.filter(r => r.id !== reportId);
    localStorage.setItem(reportsKey, JSON.stringify(updatedReports));
    
    // 현재 선택된 보고서가 삭제된 경우 선택 해제
    if (selectedReport.value && selectedReport.value.id === reportId) {
      selectedReport.value = null;
      report.value = "";
    }
    
    // 목록 새로고침
    await loadList();
    
    showDeleteConfirm.value = false;
    reportToDelete.value = null;
  } catch (error) {
    console.error('보고서 삭제 중 오류:', error);
    alert(settingStore.language === 'ko' 
      ? '보고서 삭제 중 오류가 발생했습니다.' 
      : 'An error occurred while deleting the report.');
  }
}

// 전역 클릭 이벤트로 컨텍스트 메뉴 닫기
function handleGlobalClick(e) {
  if (!contextMenu.value.visible) return;
  closeContextMenu();
}

// ==================== Resize 기능 ====================
function startResize(event) {
  event.preventDefault();
  isResizing.value = true;
  resizeStartY.value = event.clientY;
  resizeStartHeight.value = viewerHeight.value;
  
  document.addEventListener('mousemove', handleResize);
  document.addEventListener('mouseup', stopResize);
  document.body.style.cursor = 'ns-resize';
  document.body.style.userSelect = 'none';
}

function handleResize(event) {
  if (!isResizing.value) return;
  
  const deltaY = event.clientY - resizeStartY.value;
  const newHeight = resizeStartHeight.value - deltaY; // 위로 드래그하면 높이 증가, 아래로 드래그하면 높이 감소
  
  // 최소 높이와 최대 높이 제한
  const minHeight = 300;
  const maxHeight = window.innerHeight - 100; // 상하 여백 고려
  
  viewerHeight.value = Math.max(minHeight, Math.min(maxHeight, newHeight));
}

function stopResize() {
  isResizing.value = false;
  document.removeEventListener('mousemove', handleResize);
  document.removeEventListener('mouseup', stopResize);
  document.body.style.cursor = '';
  document.body.style.userSelect = '';
}

// 컴포넌트 마운트 시 전역 클릭 리스너 추가
onMounted(() => {
  window.addEventListener('click', handleGlobalClick);
  // 초기 높이를 화면 높이의 70%로 설정
  viewerHeight.value = Math.min(800, window.innerHeight * 0.7);
});

onBeforeUnmount(() => {
  window.removeEventListener('click', handleGlobalClick);
  // Resize 이벤트 리스너 정리
  if (isResizing.value) {
    stopResize();
  }
});
</script>
