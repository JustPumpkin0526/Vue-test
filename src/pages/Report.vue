<template>
  <div class="w-full h-[95vh] bg-gradient-to-br from-slate-200 to-slate-300 via-slate-100 p-10 overflow-hidden">
    <div class="grid lg:grid-cols-[1fr_400px] gap-6 h-full">
      <!-- 좌측: 리포트 뷰어 -->
      <section
        class="rounded-2xl p-6 bg-gradient-to-br from-white via-gray-50 to-gray-100 border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-300 flex flex-col h-full min-h-0">
        <!-- 헤더 -->
        <header class="flex items-center justify-between px-1 pb-4 mb-4 border-b border-slate-800/70">
          <div class="flex flex-col gap-1">
            <div
              class="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-400/40 w-fit">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span class="text-[11px] font-semibold tracking-wide text-emerald-600 uppercase">
                Report Viewer
              </span>
            </div>
            <p class="text-xs md:text-sm text-black mt-1">
              {{ selectedReport?.title || '리포트를 선택하세요' }}
              <span v-if="selectedReport?.createdAt" class="text-gray-500 ml-2">
                · {{ formatDate(selectedReport.createdAt) }}
              </span>
            </p>
          </div>
          <div class="flex items-center gap-2">
            <button
              v-if="selectedReport"
              @click="prevPage"
              :disabled="currentPage <= 1"
              class="w-9 h-9 flex items-center justify-center bg-slate-200/70 hover:bg-slate-400/80 border border-slate-500/60 text-slate-700 rounded-lg shadow transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
              title="이전 페이지">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <button
              v-if="selectedReport"
              @click="nextPage"
              :disabled="currentPage >= totalPages"
              class="w-9 h-9 flex items-center justify-center bg-slate-200/70 hover:bg-slate-400/80 border border-slate-500/60 text-slate-700 rounded-lg shadow transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
              title="다음 페이지">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
            <button
              v-if="selectedReport"
              @click="exportFile"
              class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500/90 hover:bg-emerald-400 text-white shadow-lg shadow-emerald-500/30 transition-all duration-200 transform hover:scale-[1.03] active:scale-[0.97]">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span class="text-sm font-medium">내보내기</span>
            </button>
          </div>
        </header>

        <!-- 리포트 내용 -->
        <div
          v-if="selectedReport"
          class="flex-1 border border-gray-200 rounded-xl p-6 bg-white overflow-y-auto overflow-x-hidden shadow-inner min-h-0">
          <div class="prose prose-sm max-w-none">
            <div class="whitespace-pre-wrap text-sm leading-relaxed text-gray-800" v-html="formattedReport"></div>
          </div>
        </div>

        <!-- 빈 상태 -->
        <div v-else class="flex-1 flex items-center justify-center border border-gray-200 rounded-xl bg-gray-50">
          <div class="text-center">
            <svg class="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p class="text-gray-500 text-sm">리포트를 선택하여 내용을 확인하세요</p>
          </div>
        </div>

        <!-- 페이지 정보 -->
        <div v-if="selectedReport" class="mt-4 flex items-center justify-between text-xs text-gray-500">
          <span>페이지 {{ currentPage }} / {{ totalPages }}</span>
          <span>{{ selectedReport.wordCount || 0 }} 단어</span>
        </div>
      </section>

      <!-- 우측: 리포트 리스트 -->
      <aside
        class="rounded-2xl p-6 bg-gradient-to-br from-white via-gray-50 to-gray-100 border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-300 flex flex-col h-full min-h-0">
        <!-- 헤더 -->
        <header class="flex items-center justify-between px-1 pb-4 mb-4 border-b border-slate-800/70">
          <div class="flex flex-col gap-1">
            <div
              class="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-blue-500/10 border border-blue-400/40 w-fit">
              <span class="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse"></span>
              <span class="text-[11px] font-semibold tracking-wide text-blue-600 uppercase">
                Report Library
              </span>
            </div>
            <p class="text-xs text-black mt-1">총 {{ totalReports }}개의 리포트</p>
          </div>
        </header>

        <!-- 검색 및 필터 -->
        <div class="mb-4 space-y-2">
          <div class="relative">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="리포트 검색..."
              class="w-full rounded-xl border border-slate-300 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-300 px-4 py-2.5 pl-10 bg-white text-sm transition-all"
              @input="handleSearch" />
            <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none"
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
                  ? 'bg-emerald-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              ]">
              최신순
            </button>
            <button
              @click="sortBy = 'title'"
              :class="[
                'px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
                sortBy === 'title'
                  ? 'bg-emerald-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              ]">
              제목순
            </button>
          </div>
        </div>

        <!-- 리포트 리스트 -->
        <div class="flex-1 overflow-y-auto space-y-3">
          <div v-if="filteredList.length === 0" class="text-center py-12">
            <svg class="w-12 h-12 mx-auto text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p class="text-gray-500 text-sm">리포트가 없습니다</p>
          </div>

          <div
            v-for="r in filteredList"
            :key="r.id"
            @click="open(r)"
            :class="[
              'group p-4 border rounded-xl cursor-pointer transition-all duration-200',
              selectedReport?.id === r.id
                ? 'bg-emerald-50 border-emerald-300 shadow-md'
                : 'bg-white border-gray-200 hover:border-emerald-300 hover:shadow-md'
            ]">
            <div class="flex items-start justify-between gap-3">
              <div class="flex-1 min-w-0">
                <h4 class="font-semibold text-sm text-gray-900 mb-1 truncate group-hover:text-emerald-600 transition-colors">
                  {{ r.title || '제목 없음' }}
                </h4>
                <p v-if="r.description" class="text-xs text-gray-600 line-clamp-2 mb-2">
                  {{ r.description }}
                </p>
                <div class="flex items-center gap-3 text-xs text-gray-500">
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
                    {{ r.wordCount }} 단어
                  </span>
                </div>
              </div>
              <button
                @click.stop="open(r)"
                class="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-600 rounded-lg transition-all opacity-0 group-hover:opacity-100">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- 페이지네이션 -->
        <div class="mt-4 pt-4 border-t border-gray-200">
          <Pagination :page="page" :pages="pages" @update:page="(p) => { page = p; loadList(); }" />
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import Pagination from "@/components/Pagination.vue";
import api from "@/services/api";
import { marked } from 'marked';

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
      title: "2024년 3월 수사 사고 보고서",
      description: "2024년 3월 중 CCTV 영상 분석을 통한 수사 사고 발생 현황 및 대응 조치 보고서입니다.",
      content: "# 수사 사고 보고서\n\n**보고일시**: 2024년 3월 31일\n**보고자**: 수사과\n**보고대상**: 경찰청장\n\n---\n\n## 1. 개요\n\n본 보고서는 2024년 3월 한 달간 CCTV 영상 분석 시스템을 통하여 감지된 수사 사고 및 보안 위협 사건에 대한 종합 보고서입니다.\n\n## 2. 사고 발생 현황\n\n### 2.1 전체 통계\n\n- **총 감지 건수**: 23건\n- **중대 사건**: 5건\n- **일반 사건**: 18건\n- **무기 관련 사건**: 3건\n- **폭력 사건**: 8건\n- **절도 사건**: 7건\n- **기타 의심 행위**: 5건\n\n### 2.2 시간대별 발생 현황\n\n- **심야 시간대 (00:00~06:00)**: 12건 (52.2%)\n- **주간 시간대 (06:00~18:00)**: 7건 (30.4%)\n- **저녁 시간대 (18:00~24:00)**: 4건 (17.4%)\n\n## 3. 주요 사건 상세\n\n### 3.1 중대 사건\n\n#### 사건 1: 무기 휴대 의심 행위\n- **발생 시각**: 2024년 3월 15일 02:34:12\n- **위치**: 상업지구 A구역\n- **내용**: 남성 1명이 칼로 추정되는 물체를 휴대한 채 주변을 배회하는 행위가 감지됨\n- **대응 조치**: 즉시 현장 경찰 파견, 해당 인물 신원 확인 및 검문 실시\n- **결과**: 경고 조치 후 퇴거, 추가 모니터링 지시\n\n#### 사건 2: 폭력 행위\n- **발생 시각**: 2024년 3월 22일 19:45:30\n- **위치**: 주거지역 B동 입구\n- **내용**: 다수의 인물 간 신체적 충돌 및 폭행 행위 감지\n- **대응 조치**: 신고 접수 후 경찰 출동, 현장 제압 및 관계자 연행\n- **결과**: 관련자 3명 입건, 피해자 1명 병원 이송\n\n#### 사건 3: 절도 사건\n- **발생 시각**: 2024년 3월 28일 03:12:45\n- **위치**: 상점가 C상점\n- **내용**: 야간 시간대 유리문 파손 후 침입, 상품 절취 행위 감지\n- **대응 조치**: 현장 보존 및 수사 착수, CCTV 영상 분석을 통한 용의자 추적\n- **결과**: 용의자 2명 검거, 절취 물품 회수\n\n### 3.2 무기 관련 사건\n\n- **총기류 의심**: 1건 (추가 조사 중)\n- **칼 등 날카로운 도구**: 2건 (경고 조치 완료)\n\n### 3.3 폭력 사건\n\n- **신체적 폭행**: 5건\n- **협박 및 위협 행위**: 3건\n\n## 4. 대응 조치 현황\n\n### 4.1 즉시 대응\n\n- **경찰 출동**: 15건\n- **현장 제압**: 8건\n- **관계자 연행**: 5건\n\n### 4.2 사후 조치\n\n- **수사 착수**: 12건\n- **용의자 검거**: 7건\n- **추가 모니터링 지시**: 6건\n\n## 5. 시스템 운영 현황\n\n### 5.1 영상 분석 시스템\n\n- **분석 대상 영상**: 총 1,247시간\n- **자동 감지 정확도**: 87.3%\n- **오탐률**: 12.7%\n- **평균 분석 시간**: 영상 1시간당 약 3분 24초\n\n### 5.2 개선 사항\n\n- 무기 감지 알고리즘 정확도 향상 필요\n- 야간 시간대 영상 화질 개선 검토\n- 실시간 알림 시스템 응답 속도 개선\n\n## 6. 향후 계획\n\n1. **시스템 고도화**: AI 기반 위협 행위 예측 모델 도입 검토\n2. **인력 배치**: 심야 시간대 순찰 인력 증원\n3. **협력 체계**: 지역 주민 자율 방범대와의 협력 강화\n4. **예방 활동**: 취약 지역 집중 관리 및 보안 시설 보강\n\n## 7. 결론\n\n2024년 3월 중 CCTV 영상 분석을 통하여 총 23건의 수사 사고가 감지되었으며, 이 중 5건의 중대 사건에 대하여 신속한 대응을 실시하였습니다. 특히 무기 관련 사건과 폭력 사건에 대하여 사전 예방 및 즉시 대응 체계가 효과적으로 작동한 것으로 평가됩니다.\n\n다만, 야간 시간대 발생 빈도가 높은 점을 고려하여 해당 시간대의 순찰 강화 및 보안 시설 보완이 필요합니다.\n\n---\n\n**보고서 작성**: 수사과장\n**승인**: 경찰청장",
      createdAt: "2024-03-31T10:00:00Z",
      wordCount: 850
    },
    {
      id: 2,
      title: "2024년 3월 4주차 수사 사고 보고서",
      description: "2024년 3월 4주차(3월 25일~31일) 동안 발생한 수사 사고 현황 보고서입니다.",
      content: "# 수사 사고 보고서\n\n**보고일시**: 2024년 3월 31일\n**보고기간**: 2024년 3월 25일 ~ 3월 31일\n**보고자**: 수사과\n**보고대상**: 경찰청장\n\n---\n\n## 1. 개요\n\n본 보고서는 2024년 3월 4주차(3월 25일~31일) 동안 CCTV 영상 분석을 통하여 감지된 수사 사고 및 보안 위협 사건에 대한 주간 보고서입니다.\n\n## 2. 주간 사고 발생 현황\n\n### 2.1 전체 통계\n\n- **총 감지 건수**: 8건\n- **중대 사건**: 2건\n- **일반 사건**: 6건\n- **무기 관련 사건**: 1건\n- **폭력 사건**: 3건\n- **절도 사건**: 2건\n- **의심 행위**: 2건\n\n### 2.2 일별 발생 현황\n\n- **3월 25일**: 1건 (절도)\n- **3월 26일**: 2건 (폭력 1건, 의심 행위 1건)\n- **3월 27일**: 0건\n- **3월 28일**: 2건 (절도 1건, 무기 관련 1건)\n- **3월 29일**: 1건 (폭력)\n- **3월 30일**: 1건 (폭력)\n- **3월 31일**: 1건 (의심 행위)\n\n## 3. 주요 사건 상세\n\n### 3.1 중대 사건\n\n#### 사건 1: 상점 침입 절도\n- **발생 일시**: 2024년 3월 28일 03:12:45\n- **위치**: 상점가 C상점\n- **내용**: 야간 시간대 유리문 파손 후 침입, 상품 절취 행위가 CCTV를 통해 감지됨\n- **대응 조치**: 즉시 현장 경찰 파견, 현장 보존 및 수사 착수\n- **결과**: 용의자 2명 검거, 절취 물품 전량 회수\n\n#### 사건 2: 무기 휴대 의심 행위\n- **발생 일시**: 2024년 3월 28일 22:15:30\n- **위치**: 주거지역 D구역\n- **내용**: 남성 1명이 칼로 추정되는 물체를 휴대한 채 주거지역을 배회하는 행위 감지\n- **대응 조치**: 신속 출동 및 해당 인물 검문 실시\n- **결과**: 경고 조치 후 퇴거, 추가 모니터링 지시\n\n### 3.2 일반 사건\n\n- **폭력 사건**: 3건 (모두 현장 제압 완료)\n- **절도 사건**: 1건 (수사 진행 중)\n- **의심 행위**: 2건 (추가 모니터링 중)\n\n## 4. 대응 조치 현황\n\n### 4.1 즉시 대응\n\n- **경찰 출동**: 6건\n- **현장 제압**: 3건\n- **관계자 연행**: 2건\n\n### 4.2 사후 조치\n\n- **수사 착수**: 5건\n- **용의자 검거**: 2건\n- **추가 모니터링**: 3건\n\n## 5. 특이 사항\n\n1. **야간 시간대 집중 발생**: 8건 중 5건이 심야 시간대(00:00~06:00)에 발생\n2. **상점가 지역 집중**: 상점가 지역에서 3건 발생하여 해당 지역 순찰 강화 필요\n3. **무기 관련 사건 증가**: 전주 대비 무기 관련 의심 행위 1건 증가\n\n## 6. 향후 대응 계획\n\n1. **야간 순찰 강화**: 심야 시간대 순찰 인력 증원 및 순찰 빈도 증가\n2. **상점가 집중 관리**: 상점가 지역 CCTV 추가 설치 및 보안 시설 보강\n3. **무기 감지 시스템 개선**: 무기 감지 알고리즘 정확도 향상 작업 진행\n\n## 7. 결론\n\n2024년 3월 4주차 동안 총 8건의 수사 사고가 감지되었으며, 이 중 2건의 중대 사건에 대하여 신속한 대응을 실시하였습니다. 특히 절도 사건의 경우 용의자를 신속히 검거하여 피해를 최소화할 수 있었습니다.\n\n다만, 야간 시간대와 상점가 지역에서의 사건 발생이 집중되고 있어 해당 지역에 대한 집중 관리가 필요합니다.\n\n---\n\n**보고서 작성**: 수사과장\n**승인**: 경찰청장",
      createdAt: "2024-03-30T14:30:00Z",
      wordCount: 650
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

function formatDate(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString('ko-KR', {
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

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.prose {
  color: #374151;
}

.prose :deep(h1) {
  font-size: 1.875rem;
  font-weight: 700;
  margin-top: 0;
  margin-bottom: 1rem;
  color: #111827;
}

.prose :deep(h2) {
  font-size: 1.5rem;
  font-weight: 600;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  color: #1f2937;
}

.prose :deep(h3) {
  font-size: 1.25rem;
  font-weight: 600;
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
  color: #374151;
}

.prose :deep(p) {
  margin-bottom: 1rem;
  line-height: 1.75;
}

.prose :deep(ul),
.prose :deep(ol) {
  margin-bottom: 1rem;
  padding-left: 1.5rem;
}

.prose :deep(li) {
  margin-bottom: 0.5rem;
}

.prose :deep(code) {
  background-color: #f3f4f6;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.875em;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
}

.prose :deep(pre) {
  background-color: #1f2937;
  color: #f9fafb;
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin-bottom: 1rem;
}

.prose :deep(pre code) {
  background-color: transparent;
  padding: 0;
  color: inherit;
}

.prose :deep(blockquote) {
  border-left: 4px solid #10b981;
  padding-left: 1rem;
  margin-left: 0;
  margin-bottom: 1rem;
  color: #6b7280;
  font-style: italic;
}
</style>
