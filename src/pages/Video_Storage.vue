<template>
  <!-- 메뉴 틀 -->
  <div id="video_list" class="w-[100%] h-[90%]">
    <header id="header" class="flex items-center justify-between">
      <div class="w-[20%] bg-blue-400 text-white text-[25px] p-3 text-center rounded-lg shadow-md mt-[10px] ml-[50px]">
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
    <div id="list" class="flex w-full h-full border-[1px] border-black bg-gray-300 rounded-[12px] p-6 mt-6">
      <div class="w-full h-[90%] border-[1px] border-black bg-white rounded-[12px] overflow-y-auto">
        <div v-if="items.length === 0" class="flex items-center justify-center h-full">
          <div
            class="w-[30%] h-[9%] bg-gray-200 text-gray-600 text-center text-[24px] pt-[22px] border-[1px] border-black rounded-lg shadow-md">
            please Upload the video
          </div>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6 p-6">
          <div v-for="video in items" :key="video.id"
            class="flex flex-col items-center justify-center bg-gray-100 rounded-lg shadow hover:bg-blue-100 cursor-pointer p-3 border border-gray-300 relative"
            @click="toggleSelect(video.id)">
            <div
              class="w-[100%] h-[100%] flex items-center justify-center bg-gray-300 rounded mb-2 overflow-hidden relative"
              @mouseenter="hoveredVideoId = video.id" @mouseleave="hoveredVideoId = null">
              <input type="checkbox" class="absolute top-1 left-1 z-10" v-model="selectedIds" :value="video.id" />
              <video :ref="el => (videoRefs[video.id] = el)" v-if="video.displayUrl" :src="video.displayUrl"
                class="object-cover rounded" preload="metadata" @timeupdate="updateProgress(video.id, $event)"></video>
              <span v-else class="text-gray-400">No Thumbnail</span>
              <div v-if="video.title"
                class="absolute top-1 right-1 bg-black bg-opacity-60 text-white text-xs px-2 py-1 rounded truncate max-w-[70%] pointer-events-none">
                {{ video.title }}
              </div>
              <!-- 재생 버튼 -->
              <button @click.stop="togglePlay(video.id)" :class="{
                'opacity-100': hoveredVideoId === video.id || !playingVideoIds.includes(video.id),
                'opacity-0': hoveredVideoId !== video.id && playingVideoIds.includes(video.id),
              }"
                class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 text-white rounded-full w-12 h-12 m-auto transition-opacity duration-300">
                <svg v-if="!playingVideoIds.includes(video.id)" xmlns="http://www.w3.org/2000/svg" fill="currentColor"
                  viewBox="0 0 16 16" class="w-8 h-8">
                  <path
                    d="M6.271 4.055a.5.5 0 0 1 .759-.429l4.592 3.11a.5.5 0 0 1 0 .828l-4.592 3.11a.5.5 0 0 1-.759-.429V4.055z" />
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 16 16" class="w-8 h-8">
                  <path
                    d="M5.5 3.5A.5.5 0 0 1 6 3h1a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5H6a.5.5 0 0 1-.5-.5v-9zM9.5 3.5A.5.5 0 0 1 10 3h1a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-9z" />
                </svg>
              </button>
            </div>
            <!-- 프로그레스 바 -->
            <div class="w-full h-2 bg-gray-300 rounded-full overflow-hidden relative cursor-pointer"
              @click.stop="seekVideo(video.id, $event)">
              <div class="h-full bg-blue-500" :style="{ width: `${video.progress || 0}%` }"></div>
              <div class="absolute top-0 h-4 w-4 bg-white rounded-full shadow transform -translate-y-1/2"
                :style="{ left: `${video.progress || 0}%` }" @mousedown="startDragging(video.id, $event)"></div>
            </div>
            <!-- 확대 모달 -->
            <div v-if="isZoomed" class="fixed inset-0 z-[200] flex items-center justify-center bg-black bg-opacity-40"
              @click.stop>
              <div
                class="bg-white rounded-xl shadow-xl p-6 min-w-[350px] max-w-[90vw] relative flex flex-col items-center">
                <div class="relative w-full h-[400px] mb-2">
                  <video v-if="zoomedVideo" :src="zoomedVideo.displayUrl" class="w-full h-full rounded-xl"
                    controls></video>
                  <div v-if="zoomedVideo"
                    class="absolute top-2 left-2 bg-gray-300 text-black text-xs px-2 py-1 rounded truncate max-w-[70%] pointer-events-none">
                    {{ zoomedVideo.title }}
                  </div>
                </div>
                <button class="px-3 py-2 rounded-md bg-gray-300 text-black mb-2 hover:bg-gray-400 transition-colors"
                  @click="unzoomVideo">닫기</button>
              </div>
            </div>
            <!-- 설정 버튼 -->
            <div
              class="relative top-[2%] left-[47%] flex flex-col cursor-pointer bg-[#787878] p-2 rounded hover:bg-gray-600"
              @click.stop="openSettings(video.id)">
              <span class="w-[3.5px] h-[3.5px] bg-white rounded-full mb-[2px]"></span>
              <span class="w-[3.5px] h-[3.5px] bg-white rounded-full mb-[2px]"></span>
              <span class="w-[3.5px] h-[3.5px] bg-white rounded-full"></span>
            </div>
            <div v-if="expandedVideoId === video.id"
              class="absolute bottom-[15px] right-[40px] flex flex-col items-center">
              <button
                class="bg-blue-500 hover:bg-blue-600 text-white text-s font-semibold px-3 py-1 rounded-lg shadow-lg transition-transform transform hover:scale-105"
                @click.stop="zoomVideo(video)">
                확대
              </button>
            </div>
          </div>
        </div>
      </div>
      <!-- 좌측 하단 Summary, Search 버튼 -->
      <div class="fixed left-[13%] bottom-[7%] w-[21%] z-50 flex gap-4">
        <button
          class="w-[100%] text-[25px] px-5 py-3 rounded-lg bg-blue-500 text-white shadow-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:text-gray-100"
          :disabled="selectedIds.length === 0" @click="goToSummary">Summary</button>
        <button
          class="w-[100%] text-[25px] px-5 py-3 rounded-lg bg-green-500 text-white shadow-lg hover:bg-green-600 disabled:bg-gray-400 disabled:text-gray-100"
          :disabled="selectedIds.length === 0" @click="goToSearch">Search</button>
      </div>

      <!-- 우측 하단 선택 동영상 삭제 버튼 -->
      <div class="fixed right-[3%] bottom-[7%] w-[14%] z-50">
        <button class="w-[100%] text-[25px] px-5 py-3 rounded-lg bg-red-500 text-white shadow-lg hover:bg-red-600"
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

      <!-- Search 사이드바 메뉴 -->
      <!-- 배경 오버레이 -->
      <Transition name="overlay">
        <div v-if="showSearchSidebar" class="fixed inset-0 z-[150] bg-black bg-opacity-40" @click="closeSearchSidebar">
        </div>
      </Transition>

      <!-- 사이드바 패널 -->
      <Transition name="sidebar">
        <div v-if="showSearchSidebar" class="fixed top-0 right-0 z-[151] bg-white w-[70%] h-full shadow-xl" @click.stop>
          <!-- 사이드바 헤더 -->
          <div class="flex items-center justify-between p-4 border-b">
            <h2 class="text-lg font-semibold">Search Videos</h2>
            <button @click="closeSearchSidebar" class="p-2 hover:bg-gray-100 rounded-full transition-colors">
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
import { ref, onMounted, onActivated } from "vue";
import { useRouter } from 'vue-router';
import { useSummaryVideoStore } from '@/stores/summaryVideoStore';

const isZoomed = ref(false);
const zoomedVideo = ref(null);
const showSearchSidebar = ref(false);
const hoveredVideoId = ref(null);
const playingVideoIds = ref([]);
const expandedVideoId = ref(null);
const showDeletePopup = ref(false);
const items = ref([]);
const selectedIds = ref([]);
const videoRefs = ref({});
const isDragging = ref(false);
const draggedVideoId = ref(null);

const router = useRouter();
const summaryVideoStore = useSummaryVideoStore();

onMounted(loadVideosFromStorage);
onActivated(() => {
  if (items.value.length === 0) {
    loadVideosFromStorage();
  }
});

function loadVideosFromStorage() {
  const stored = localStorage.getItem("videoItems");
  if (!stored) return;
  items.value = JSON.parse(stored).map(v => ({
    ...v,
    originUrl: v.url || v.originUrl || '',
    displayUrl: v.url || v.displayUrl || v.originUrl || '',
    objectUrl: null,
    progress: 0
  }));
}

function persistToStorage() {
  localStorage.setItem("videoItems", JSON.stringify(items.value.map(({ id, title, originUrl, date }) => ({ id, title, url: originUrl, date }))));
}

function handleUpload(e) {
  const files = Array.from(e.target.files ?? []).filter((file) => {
    if (!file.type.startsWith('video/')) {
      alert('동영상 파일만 업로드할 수 있습니다.');
      return false;
    }
    return true;
  });

  const newVideos = files.map((file) => {
    const objUrl = URL.createObjectURL(file);
    return {
      id: Date.now() + Math.random(),
      title: file.name,
      originUrl: objUrl,
      displayUrl: objUrl,
      objectUrl: objUrl,
      date: new Date().toISOString().slice(0, 10),
      file,
      url: objUrl
    };
  });

  items.value.unshift(...newVideos);
  persistToStorage();
  if (e.target) e.target.value = '';
}

function toggleSelect(id) {
  const idx = selectedIds.value.indexOf(id);
  idx === -1 ? selectedIds.value.push(id) : selectedIds.value.splice(idx, 1);
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
  console.log("Selected IDs before delete:", selectedIds.value);
  console.log("Items before delete:", items.value);

  // 선택된 동영상 삭제
  items.value = items.value.filter(video => {
    if (selectedIds.value.includes(video.id)) {
      if (video.objectUrl) {
        try {
          URL.revokeObjectURL(video.objectUrl);
        } catch (error) {
          console.error("Failed to revoke object URL:", error);
        }
      }
      return false; // 삭제 대상
    }
    return true; // 유지 대상
  });

  console.log("Items after delete:", items.value);

  // localStorage 업데이트
  persistToStorage();

  // 선택된 ID 초기화
  selectedIds.value = [];
  showDeletePopup.value = false;
}

function goToSummary() {
  const selectedVideos = items.value.filter(v => selectedIds.value.includes(v.id)).map(v => ({
    ...v,
    name: v.title,
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

function togglePlay(videoId) {
  const videoElement = videoRefs.value[videoId];
  if (!videoElement) return;

  const index = playingVideoIds.value.indexOf(videoId);
  index === -1 ? playingVideoIds.value.push(videoId) && videoElement.play() : playingVideoIds.value.splice(index, 1) && videoElement.pause();
}

function openSettings(videoId) {
  expandedVideoId.value = expandedVideoId.value === videoId ? null : videoId;
}

function updateProgress(videoId, event) {
  const video = items.value.find(v => v.id === videoId);
  if (video) {
    const { currentTime, duration } = event.target;
    video.progress = duration ? (currentTime / duration) * 100 : 0;
  }
}

function seekVideo(videoId, event) {
  const videoElement = videoRefs.value[videoId];
  if (!videoElement) return;

  const { left, width } = event.currentTarget.getBoundingClientRect();
  videoElement.currentTime = ((event.clientX - left) / width) * videoElement.duration;
}

function startDragging(videoId) {
  isDragging.value = true;
  draggedVideoId.value = videoId;

  document.addEventListener('mousemove', handleDragging);
  document.addEventListener('mouseup', stopDragging);
}

function handleDragging(event) {
  if (!isDragging.value || !draggedVideoId.value) return;

  const videoElement = videoRefs.value[draggedVideoId.value];
  if (!videoElement) return;

  const progressBar = event.target.closest('.relative.cursor-pointer');
  if (!progressBar) return;

  const { left, width } = progressBar.getBoundingClientRect();
  videoElement.currentTime = Math.max(0, Math.min(((event.clientX - left) / width) * videoElement.duration, videoElement.duration));
}

function stopDragging() {
  isDragging.value = false;
  draggedVideoId.value = null;

  document.removeEventListener('mousemove', handleDragging);
  document.removeEventListener('mouseup', stopDragging);
}
</script>
