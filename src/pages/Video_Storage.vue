<template>
  <!-- 메뉴 틀 -->
  <div id="video_list" class="w-[100%] h-[90%]">
    <header id="header" class="flex items-center justify-between">
      <div class="w-[500px] bg-blue-400 text-white text-lg p-3 text-center rounded-lg shadow-md mt-6 ml-12">
        <p>My Video Storage</p>
      </div>
      <div class="flex items-center h-12 mr-12 mt-auto ml-auto">
        <label
          class="bg-blue-400 hover:bg-blue-600 text-white px-4 py-2 rounded-lg shadow cursor-pointer flex items-center">
          <span>Upload Video</span>
          <input type="file" accept="video/*" multiple class="hidden" @change="handleUpload" />
        </label>
      </div>
    </header>
    <!-- 비디오 리스트 -->
    <div id="list" class="w-full h-full border-[1px] border-black bg-gray-300 rounded-[12px] p-6 mt-6">
      <div class="w-full border-[1px] border-black bg-white rounded-[12px] overflow-y-auto"
        style="height:900px; min-height:900px; max-height:900px;">
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6 p-6">
          <div v-for="video in items" :key="video.id"
            class="flex flex-col items-center justify-center bg-gray-100 rounded-lg shadow hover:bg-blue-100 cursor-pointer p-3 border border-gray-300"
            @click="toggleSelect(video.id)">
            <div
              class="w-[100%] h-[100%] flex items-center justify-center bg-gray-300 rounded mb-2 overflow-hidden relative">
              <input type="checkbox" class="absolute top-1 left-1 z-10" v-model="selectedIds" :value="video.id" />
              <video v-if="video.displayUrl" :src="video.displayUrl" class="object-cover rounded" controls preload="metadata"></video>
              <span v-else class="text-gray-400">No Thumbnail</span>
              <div v-if="video.title"
                class="absolute top-1 right-1 bg-black bg-opacity-60 text-white text-xs px-2 py-1 rounded truncate max-w-[70%] pointer-events-none">
                {{ video.title }}
              </div>
            </div>
            <div class="flex gap-2 mt-1">
              <button @click.stop="zoomVideo(video)"
                class="px-3 py-1 rounded-md bg-blue-500 text-white font-semibold text-xs border border-blue-600 shadow hover:bg-blue-600 hover:scale-105 transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-blue-300">
                확대
              </button>
            </div>
            <!-- 확대 모달 -->
            <div v-if="isZoomed" class="fixed inset-0 z-[200] flex items-center justify-center bg-black bg-opacity-40"
              @click.stop>
              <div
                class="bg-white rounded-xl shadow-xl p-6 min-w-[350px] max-w-[90vw] relative flex flex-col items-center">
                <div class="relative w-full h-[400px] mb-2">
                  <video v-if="zoomedVideo" :src="zoomedVideo.displayUrl" class="w-full h-full rounded-xl" controls></video>
                  <div v-if="zoomedVideo"
                    class="absolute top-2 left-2 bg-gray-300 text-black text-xs px-2 py-1 rounded truncate max-w-[70%] pointer-events-none">
                    {{ zoomedVideo.title }}
                  </div>
                </div>
                <button class="px-3 py-2 rounded-md bg-gray-300 text-black mb-2 hover:bg-gray-400 transition-colors"
                  @click="unzoomVideo">닫기</button>
              </div>
            </div>
          </div>
        </div>
      </div>
      <!-- 우측 하단 선택 동영상 삭제 버튼 -->
      <div class="fixed bottom-[110px] right-[80px] z-50">
        <button class="px-5 py-3 rounded-lg bg-red-500 text-white shadow-lg hover:bg-red-600"
          :disabled="selectedIds.length === 0" @click="showDeletePopup = true">
          선택 동영상 삭제 ({{ selectedIds.length }})
        </button>
      </div>

      <!-- 중앙 팝업창 -->
      <div v-if="showDeletePopup" class="fixed inset-0 flex items-center justify-center z-[100] bg-black bg-opacity-40">
        <div class="bg-white rounded-xl shadow-xl p-8 min-w-[350px] max-w-[90vw] relative">
          <div class="text-lg font-semibold mb-4 text-center">
            {{ selectedIds.length }}개의 동영상이 삭제됩니다.<br>진행하시겠습니까?
          </div>
          <div class="flex justify-end gap-3 mt-8">
            <button class="px-5 py-2 rounded-lg bg-red-500 text-white hover:bg-red-600"
              @click="confirmDelete">delete</button>
            <button class="px-5 py-2 rounded-lg bg-gray-300 text-black hover:bg-gray-400"
              @click="showDeletePopup = false">cancel</button>
          </div>
        </div>
      </div>

      <!-- 좌측 하단 Summary, Search 버튼 -->
      <div class="fixed bottom-[110px] left-[290px] z-50 flex gap-4">
        <button
          class="w-[200px] text-[18px] px-5 py-3 rounded-lg bg-blue-500 text-white shadow-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:text-white"
          :disabled="selectedIds.length === 0" @click="goToSummary">Summary</button>
        <button
          class="w-[200px] text-[18px] px-5 py-3 rounded-lg bg-green-500 text-white shadow-lg hover:bg-green-600 disabled:bg-gray-400 disabled:text-white"
          :disabled="selectedIds.length === 0" @click="goToSearch">Search</button>
      </div>

      <!-- Search 사이드바 메뉴 -->
      <!-- 배경 오버레이 -->
      <Transition name="overlay">
        <div v-if="showSearchSidebar" 
             class="fixed inset-0 z-[150] bg-black bg-opacity-40"
             @click="closeSearchSidebar"></div>
      </Transition>
      
      <!-- 사이드바 패널 -->
      <Transition name="sidebar">
        <div v-if="showSearchSidebar" 
             class="fixed top-0 right-0 z-[151] bg-white w-[70%] h-full shadow-xl"
             @click.stop>
          <!-- 사이드바 헤더 -->
          <div class="flex items-center justify-between p-4 border-b">
            <h2 class="text-lg font-semibold">Search Videos</h2>
            <button @click="closeSearchSidebar" 
                    class="p-2 hover:bg-gray-100 rounded-full transition-colors">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
          
          <!-- 검색 입력 -->
          <div class="p-4">
            <div class="mb-4">
              <label class="block text-sm font-medium mb-2">검색어</label>
              <input type="text" placeholder="검색할 키워드를 입력하세요..."
                     class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
            </div>
            
            <!-- 선택된 동영상 목록 -->
            <div class="mb-4">
              <label class="block text-sm font-medium mb-2">선택된 동영상 ({{ selectedIds.length }}개)</label>
              <div class="max-h-48 overflow-y-auto border rounded-md">
                <div v-for="video in items.filter(v => selectedIds.includes(v.id))" :key="video.id"
                     class="flex items-center gap-3 p-2 border-b last:border-b-0">
                  <video :src="video.displayUrl" class="w-12 h-8 object-cover rounded"></video>
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium truncate">{{ video.title }}</p>
                    <p class="text-xs text-gray-500">{{ video.date }}</p>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 검색 옵션 -->
            <div class="mb-4">
              <label class="block text-sm font-medium mb-2">검색 옵션</label>
              <div class="space-y-2">
                <label class="flex items-center">
                  <input type="checkbox" class="mr-2">
                  <span class="text-sm">제목으로 검색</span>
                </label>
                <label class="flex items-center">
                  <input type="checkbox" class="mr-2">
                  <span class="text-sm">내용으로 검색</span>
                </label>
                <label class="flex items-center">
                  <input type="checkbox" class="mr-2">
                  <span class="text-sm">날짜로 검색</span>
                </label>
              </div>
            </div>
            
            <!-- 검색 버튼 -->
            <button class="w-full px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 transition-colors">
              검색 실행
            </button>
          </div>
        </div>
      </Transition>

    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from 'vue-router';
import { onMounted, onActivated } from 'vue'; // Video_List 메뉴 진입 시 동영상 목록 갱신 (router navigation guard)

onMounted(() => {
  loadVideosFromStorage();
});
onActivated(() => {
  // 이미 메모리에 파일 객체들이 유지되고 있다면 재로딩으로 File 손실 방지
  if (items.value.length === 0) {
    loadVideosFromStorage();
  }
});

const isZoomed = ref(false);
const zoomedVideo = ref(null);
const showSearchSidebar = ref(false);

const router = useRouter();
const showDeletePopup = ref(false);
const items = ref([]);
const selectedIds = ref([]);

// localStorage에서 동영상 목록 로딩
function loadVideosFromStorage() {
  const stored = localStorage.getItem("videoItems");
  if (!stored) return;
  const raw = JSON.parse(stored);
  // 기존 구조(url) -> 확장 구조(originUrl/displayUrl/objectUrl)
  items.value = raw.map(v => ({
    id: v.id,
    title: v.title,
    originUrl: v.url || v.originUrl || '',
    displayUrl: v.url || v.displayUrl || v.originUrl || '',
    objectUrl: null, // 재로딩된 세션에서는 revoke 대상 없음
    date: v.date,
    file: null
  }));
}

// 페이지 로드 시 동영상 목록 불러오기
loadVideosFromStorage();

async function handleUpload(e) {
  const files = Array.from(e.target.files ?? []);
  if (!files.length) return;
  const newVideos = files
    .filter(file => {
      if (!file.type.startsWith('video/')) {
        alert('동영상 파일만 업로드할 수 있습니다.');
        return false;
      }
      return true;
    })
    .map(file => {
      const objUrl = URL.createObjectURL(file);
      return {
        id: Date.now() + Math.random(),
        title: file.name,
        originUrl: objUrl,
        displayUrl: objUrl,
        objectUrl: objUrl, // revoke 대상
        date: new Date().toISOString().slice(0, 10),
        file,
        url: objUrl // Summary 호환(기존 필드 유지)
      };
    });
  items.value.unshift(...newVideos);
  persistToStorage();
  if (e.target) e.target.value = '';
}

function persistToStorage() {
  const serializable = items.value.map(v => ({
    id: v.id,
    title: v.title,
    url: v.originUrl, // 이전 구조와 호환
    date: v.date
  }));
  localStorage.setItem("videoItems", JSON.stringify(serializable));
}

function toggleSelect(id) {
  const idx = selectedIds.value.indexOf(id);
  if (idx === -1) {
    selectedIds.value.push(id);
  } else {
    selectedIds.value.splice(idx, 1);
  }
}

function zoomVideo(video) {
  zoomedVideo.value = video;
  isZoomed.value = true;
}

function unzoomVideo() {
  isZoomed.value = false;
  zoomedVideo.value = null;
}

function confirmDelete() {
  // 삭제 전 이 컴포넌트가 생성한 objectUrl만 해제
  items.value
    .filter(v => selectedIds.value.includes(v.id))
    .forEach(v => {
      if (v.objectUrl) {
        try { URL.revokeObjectURL(v.objectUrl); } catch (e) { }
      }
    });
  items.value = items.value.filter(v => !selectedIds.value.includes(v.id));
  persistToStorage();
  selectedIds.value = [];
  showDeletePopup.value = false;
}

import { useSummaryVideoStore } from '@/stores/summaryVideoStore';
const summaryVideoStore = useSummaryVideoStore();

function goToSummary() {
  // 반드시 items.value에서 선택된 동영상을 넘김 (file 객체가 살아있음)
  const selectedVideos = items.value
    .filter(v => selectedIds.value.includes(v.id))
    .map(v => ({
      id: v.id,
      name: v.title,
      title: v.title,
      url: v.originUrl, // Summary는 v.url을 사용 -> 원본 URL 전달
      date: v.date,
      summary: v.summary || '',
      file: v.file instanceof File ? v.file : null
    }));
  summaryVideoStore.setVideos(selectedVideos);
  router.push({ name: 'Summary' });
}

function goToSearch() {
  if (selectedIds.value.length > 0) {
    showSearchSidebar.value = true;
  }
}

function closeSearchSidebar() {
  showSearchSidebar.value = false;
}
</script>

<style scoped>
/* 배경 오버레이 애니메이션 */
.overlay-enter-active, .overlay-leave-active {
  transition: opacity 0.3s ease-in-out;
}

.overlay-enter-from, .overlay-leave-to {
  opacity: 0;
}

/* 사이드바 패널 애니메이션 */
.sidebar-enter-active, .sidebar-leave-active {
  transition: transform 0.3s ease-in-out;
}

.sidebar-enter-from, .sidebar-leave-to {
  transform: translateX(100%);
}
</style>
