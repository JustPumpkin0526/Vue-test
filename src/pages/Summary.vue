<template>
  <div class="grid lg:grid-cols-2 gap-6">
    <!-- 좌측: 비디오/업로드 -->
    <section class="rounded-2xl border border-black p-4 bg-gray-50">
      <h2 class="font-semibold mb-3">
        {{selectedIndexes.length === 0 ? 'Video Section' : (videoFiles.find(v => v.id === selectedIndexes[0])?.name ||
          'Video Section')}}
      </h2>


      <div
        class="aspect-video h-92 rounded-xl mb-3 flex items-center justify-center text-gray-600 transition border-2 border-black cursor-pointer"
        :class="[isDragging ? 'bg-blue-100 border-blue-400' : 'bg-gray-300 border-transparent']"
        @dragover.prevent="onDragOver" @dragleave.prevent="onDragLeave" @drop.prevent="onDrop"
        @click="onVideoAreaClick">
        <template v-if="!videoUrl">
          <span v-if="!isDragging">
            <span class="font-bold text-blue-500 flex flex-col items-center justify-center text-center w-full">
              Drop Video here<br>-- or --<br>Click to upload
            </span>
          </span>
          <span v-else class="text-blue-600 font-bold">여기에 파일을 놓으세요</span>
        </template>
        <template v-else-if="videoFiles.length === 1">
          <div class="relative w-full h-full" @mouseenter="singleVideo && (hoveredVideoId = singleVideo.id)"
            @mouseleave="hoveredVideoId = null">
            <video v-if="singleVideo" :src="singleVideo.displayUrl" class="w-full h-full rounded-xl object-cover"
              preload="metadata" :ref="el => { if (el && singleVideo) videoRefs[singleVideo.id] = el }"
              @timeupdate="updateProgress(singleVideo.id, $event)"
              @ended="singleVideo && onVideoEnded(singleVideo.id)"
              :class="{ 'brightness-75': !playingVideoIds.includes(singleVideo.id) }"></video>
            <div
              class="w-full h-2 bg-gray-300 rounded-full relative cursor-pointer"
              @click.stop="seekVideo(singleVideo.id, $event)"
              :ref="el => { if (el && singleVideo) progressBarRefs[singleVideo.id] = el }">
              <!-- 진행 채움 바 -->
              <div
                class="h-full bg-blue-500"
                :style="{ width: `${progress[singleVideo.id] || 0}%` }"
              ></div>
              <!-- 드래그 핸들: 외곽 컨테이너 기준으로 위치 고정 -->
              <div
                class="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white rounded-full border border-blue-500 cursor-pointer shadow"
                :style="{ left: `calc(${progress[singleVideo.id] || 0}% - 8px)` }"
                @mousedown="startDragging(singleVideo.id, $event)"
                @click.stop
              ></div>
            </div>
            <button v-if="singleVideo" @click.stop="togglePlay(singleVideo.id)" :class="{
              'opacity-100': hoveredVideoId === singleVideo.id || !playingVideoIds.includes(singleVideo.id),
              'opacity-0': hoveredVideoId !== singleVideo.id && playingVideoIds.includes(singleVideo.id)
            }"
              class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 text-white rounded-full w-[50px] h-[50px] m-auto transition-opacity duration-300">
              <svg v-if="!playingVideoIds.includes(singleVideo.id)" xmlns="http://www.w3.org/2000/svg"
                fill="currentColor" viewBox="0 -0.5 16 16" class="w-10 h-10">
                <path
                  d="M6.271 4.055a.5.5 0 0 1 .759-.429l4.592 3.11a.5.5 0 0 1 0 .828l-4.592 3.11a.5.5 0 0 1-.759-.429V4.055z" />
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 16 16" class="w-10 h-10">
                <path
                  d="M5.5 3.5A.5.5 0 0 1 6 3h1a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5H6a.5.5 0 0 1-.5-.5v-9zM9.5 3.5A.5.5 0 0 1 10 3h1a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-9z" />
              </svg>
            </button>
          </div>
        </template>
        <template v-else>
          <!-- 여러 개일 때 리스트 또는 확대 -->
          <div v-if="!isZoomed" id="list" class="w-full bg-gray-300 rounded-[12px] p-6">
            <div class="w-full border-[1px] border-black bg-white rounded-[12px] overflow-y-auto"
              style="height:600px; min-height:600px; max-height:600px; position: relative;">
              <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-3 gap-6 p-6">
                <div v-for="(video, idx) in videoFiles" :key="video.id"
                  class="flex flex-col items-center justify-center bg-gray-100 rounded-lg shadow hover:bg-blue-100 cursor-pointer p-3 border border-black relative"
                  @click="selectVideo(video.id)">
                  <div
                    class="w-[100%] h-[100%] flex items-center justify-center bg-gray-300 rounded mb-2 overflow-hidden relative"
                    @mouseenter="hoveredVideoId = video.id" @mouseleave="hoveredVideoId = null">
                    <input type="checkbox" class="absolute top-1 left-1 z-10" v-model="selectedIndexes"
                      :value="video.id" />
                    <video v-if="video.displayUrl" :src="video.displayUrl" class="object-cover rounded"
                      preload="metadata" :ref="el => (videoRefs[video.id] = el)" @ended="onVideoEnded(video.id)"
                      @timeupdate="updateProgress(video.id, $event)"
                      :class="{ 'brightness-75': !playingVideoIds.includes(video.id) }"></video>
                    <span v-else class="text-gray-400">No Thumbnail</span>
                    <div v-if="video.title || video.name"
                      class="absolute top-1 right-1 bg-black bg-opacity-60 text-white text-xs px-2 py-1 rounded truncate max-w-[70%] pointer-events-none">
                      {{ video.title || video.name }}
                    </div>
                    <!-- 재생/일시정지 토글 버튼 -->
                    <button @click.stop="togglePlay(video.id)" :class="{
                      'opacity-100': hoveredVideoId === video.id || !playingVideoIds.includes(video.id),
                      'opacity-0': hoveredVideoId !== video.id && playingVideoIds.includes(video.id)
                    }"
                      class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 text-white rounded-full w-12 h-12 m-auto transition-opacity duration-300">
                      <svg v-if="!playingVideoIds.includes(video.id)" xmlns="http://www.w3.org/2000/svg"
                        fill="currentColor" viewBox="0 0 16 16">
                        <path
                          d="M6.271 4.055a.5.5 0 0 1 .759-.429l4.592 3.11a.5.5 0 0 1 0 .828l-4.592 3.11a.5.5 0 0 1-.759-.429V4.055z" />
                      </svg>
                      <svg v-else xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 16 16">
                        <path
                          d="M5.5 3.5A.5.5 0 0 1 6 3h1a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5H6a.5.5 0 0 1-.5-.5v-9zM9.5 3.5A.5.5 0 0 1 10 3h1a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-9z" />
                      </svg>
                    </button>
                  </div>
                  <!-- 진행바 (멀티 비디오용) -->
                  <div class="w-full mt-1">
                    <div class="w-full h-2 bg-gray-300 rounded-full relative cursor-pointer"
                      @click.stop="seekVideo(video.id, $event)"
                      :ref="el => { if (el) progressBarRefs[video.id] = el }">
                      <div class="h-full bg-blue-500" :style="{ width: `${progress[video.id] || 0}%` }"></div>
                        <div class="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full border border-blue-500 cursor-pointer shadow"
                          :style="{ left: `calc(${progress[video.id] || 0}% - 6px)` }"
                          @mousedown="startDragging(video.id, $event)"
                          @click.stop></div>
                    </div>
                  </div>
                  <div class="flex gap-2 mt-2">
                    <button @click.stop="zoomVideo(idx)"
                      class="px-3 py-1 rounded-md bg-blue-500 text-white font-semibold text-xs border border-blue-600 shadow hover:bg-blue-600 hover:scale-105 transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-blue-300">
                      확대
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="flex flex-col items-center w-full">
            <div class="relative w-full h-[100%] mb-2">
              <video v-if="videoFiles[zoomedIndex]" :src="videoFiles[zoomedIndex].displayUrl"
                class="w-full h-[100%] rounded-xl object-cover transition-all duration-300" preload="metadata"
                :ref="el => { if (el && videoFiles[zoomedIndex]) videoRefs[videoFiles[zoomedIndex].id] = el }"
                @ended="onVideoEnded(videoFiles[zoomedIndex].id)"
                :class="{ 'brightness-75': !playingVideoIds.includes(videoFiles[zoomedIndex].id) }"></video>
              <div v-if="videoFiles[zoomedIndex]"
                class="absolute top-2 left-2 bg-gray-300 text-black text-xs px-2 py-1 rounded truncate max-w-[70%] pointer-events-none">
                {{ videoFiles[zoomedIndex].name || videoFiles[zoomedIndex].title }}
              </div>
              <!-- 재생/일시정지 토글 버튼 -->
              <button v-if="videoFiles[zoomedIndex]" @click.stop="togglePlay(videoFiles[zoomedIndex].id)" :class="{
                'opacity-100 scale-100': !playingVideoIds.includes(videoFiles[zoomedIndex].id),
                'opacity-0 scale-90': playingVideoIds.includes(videoFiles[zoomedIndex].id)
              }"
                class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 text-white rounded-full w-20 h-20 m-auto transition-all duration-300">
                <svg v-if="!playingVideoIds.includes(videoFiles[zoomedIndex].id)" xmlns="http://www.w3.org/2000/svg"
                  fill="currentColor" viewBox="0 0 16 16" class="w-10 h-10">
                  <path
                    d="M6.271 4.055a.5.5 0 0 1 .759-.429l4.592 3.11a.5.5 0 0 1 0 .828l-4.592 3.11a.5.5 0 0 1-.759-.429V4.055z" />
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 16 16"
                  class="w-10 h-10">
                  <path
                    d="M5.5 3.5A.5.5 0 0 1 6 3h1a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5H6a.5.5 0 0 1-.5-.5v-9zM9.5 3.5A.5.5 0 0 1 10 3h1a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-9z" />
                </svg>
              </button>
            </div>
            <button class="px-3 py-2 rounded-md bg-gray-300 text-black mb-2" @click="unzoomVideo">되돌아가기</button>
          </div>
        </template>
      </div>



      <!-- 프롬프트 입력 블럭 -->
      <div class="mb-3 flex items-center gap-2">
        <div class="relative flex-1">
          <textarea v-model="prompt" class="w-full border border-black rounded-md px-3 py-2 resize-none"
            placeholder="프롬프트를 입력하세요." rows="3"></textarea>
          <button
            class="absolute right-[6px] top-[56px] p-1 rounded-md bg-vix-primary text-white flex items-center justify-center"
            @click="runInference" :disabled="videoFiles.length === 0 || selectedIndexes.length === 0">
            <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0.4 -1 16 16" class="w-5 h-5">
              <path
                d="M6.271 4.055a.5.5 0 0 1 .759-.429l4.592 3.11a.5.5 0 0 1 0 .828l-4.592 3.11a.5.5 0 0 1-.759-.429V4.055z" />
            </svg>
          </button>
        </div>
      </div>

      <input type="file" accept="video/*" multiple @change="onUpload" ref="fileInputRef" class="hidden"
        :disabled="videoFiles.length > 0" />

      <div v-if="videoFiles.length === 1" class="mt-2 flex">
        <button class="px-3 py-2 rounded-md bg-red-500 text-white hover:bg-red-600 transition"
          @click="removeSingleVideo">
          동영상 삭제
        </button>
      </div>
      <div v-else-if="videoFiles.length > 1" class="mt-2 flex">
        <button class="px-3 py-2 rounded-md bg-red-500 text-white hover:bg-red-600 transition"
          @click="batchRemoveSelectedVideos" :disabled="selectedIndexes.length === 0">
          선택한 동영상 삭제
        </button>
      </div>

      <p class="text-xs text-gray-500 mt-2">
        Chunk 크기/프롬프트 등 세부 설정은 Setting에서 조정하세요.
      </p>
    </section>

    <!-- 우측: 결과/프롬프트 -->
    <section class="rounded-2xl border border-black p-4">
      <h2 class="font-semibold mb-3">요약 결과</h2>
      <!-- 채팅 형태 출력 영역 -->
      <div class="chat-window border border-black rounded-xl bg-gray-50 h-[600px] p-3 overflow-auto">
        <div v-if="chatMessages.length === 0" class="text-gray-400 text-sm flex items-center justify-center h-full">
          아직 메시지가 없습니다. 요약을 실행하거나 질문을 입력하세요.
        </div>
        <template v-else>
          <div v-for="m in chatMessages" :key="m.id" class="mb-2 flex"
            :class="m.role === 'user' ? 'justify-end' : 'justify-start'">
            <div class="bubble" :class="{
              'bubble-user': m.role === 'user',
              'bubble-assistant': m.role === 'assistant',
              'bubble-system': m.role === 'system'
            }" v-html="m.content"></div>
          </div>
        </template>
      </div>

      <div class="flex items-center gap-2 mt-3">
        <input v-model="ask_prompt" placeholder="질문을 입력하세요..."
          class="w-full rounded-xl border-[1px] border-black px-4 py-3 bg-white"
          @keyup.enter="onAsk(ask_prompt); ask_prompt = ''" />
        <button class="rounded-lg bg-vix-primary text-white px-4 py-2" @click="onAsk(ask_prompt); ask_prompt = ''">
          Ask
        </button>
      </div>

      <div class="mt-3 flex gap-2">
        <button class="px-3 py-2 rounded-md bg-gray-100" @click="saveResult">결과 저장</button>
        <button class="px-3 py-2 rounded-md bg-gray-100" @click="clear">초기화</button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from "vue";
import { useSummaryVideoStore } from '@/stores/summaryVideoStore';
import api from "@/services/api";
import { useSettingStore } from '@/stores/settingStore';
import { marked } from 'marked';

const selectedIndexes = ref([]); // 선택된 동영상 id 배열
const prompt = ref("");
const response = ref("");
// 마지막으로 요약된 비디오의 서버 video_id (다른 함수에서 재사용 가능)
const summarizedVideoId = ref(null);
// 채팅 메시지 배열: { id, role: 'user' | 'assistant' | 'system', content(html) }
const chatMessages = ref([]);
const isDragging = ref(false); // 업로드 영역 드래그 상태
const isScrubbing = ref(false); // 재생바(진행 막대) 드래그 상태
const fileInputRef = ref(null);
const ask_prompt = ref("");
const isZoomed = ref(false); // 확대 여부
const zoomedIndex = ref(null); // 확대된 동영상 인덱스
const settingStore = useSettingStore();
const videoFiles = ref([]); // Summary 메뉴의 로컬 동영상 배열
// videoUrls 제거: 템플릿에서 사용되지 않아 메모리 관리 단순화
const summaryVideoStore = useSummaryVideoStore();
// 재생 버튼 상태 (Video Storage 스타일 이식)
const hoveredVideoId = ref(null); // Track the hovered video ID
const playingVideoIds = ref([]); // 재생 중인 비디오 id 목록
const videoRefs = ref({}); // id -> video 요소
// 단일 영상 안전 접근용 computed (삭제/비움 시 에러 방지)
const singleVideo = computed(() => (videoFiles.value.length === 1 ? videoFiles.value[0] : null));
const progress = ref({});
const dragVideoId = ref(null); // 업로드 영역용 id
const draggingVideoId = ref(null); // 재생바 스크러빙 중인 비디오 id
const progressBarRefs = ref({}); // 비디오별 진행바 엘리먼트 참조
let draggingBarEl = null; // 현재 드래그 중인 진행바 엘리먼트

function updateProgress(videoId, event) {
  const video = videoRefs.value[videoId];
  if (video && video.duration) {
    progress.value[videoId] = (video.currentTime / video.duration) * 100;
  }
}

function seekVideo(videoId, event) {
  const videoElement = videoRefs.value[videoId];
  if (!videoElement) return;

  const { left, width } = event.currentTarget.getBoundingClientRect();
  videoElement.currentTime = ((event.clientX - left) / width) * videoElement.duration;
}

function startDragging(videoId, evt) {
  // 재생바 스크러빙 시작
  isScrubbing.value = true;
  draggingVideoId.value = videoId;
  // 진행바 엘리먼트 확보 (ref 사용, 없으면 이벤트 타겟에서 추론)
  draggingBarEl = progressBarRefs.value[videoId] || (evt.target && evt.target.closest('.relative.cursor-pointer'));
  document.addEventListener('mousemove', handleScrubMove);
  document.addEventListener('mouseup', stopScrubbing);
  evt.preventDefault();
}

function handleScrubMove(event) {
  if (!isScrubbing.value || !draggingVideoId.value || !draggingBarEl) return;
  const videoElement = videoRefs.value[draggingVideoId.value];
  if (!videoElement || !videoElement.duration) return;
  const { left, width } = draggingBarEl.getBoundingClientRect();
  const ratio = (event.clientX - left) / width;
  const clamped = Math.max(0, Math.min(ratio, 1));
  videoElement.currentTime = clamped * videoElement.duration;
  // 수동 진행도 업데이트 (재생 중이 아닐 때 즉시 반영)
  progress.value[draggingVideoId.value] = clamped * 100;
}

function stopScrubbing() {
  isScrubbing.value = false;
  draggingVideoId.value = null;
  draggingBarEl = null;
  document.removeEventListener('mousemove', handleScrubMove);
  document.removeEventListener('mouseup', stopScrubbing);
}

// 누락된 File 객체를 복원하기 위한 비동기 헬퍼 (object/display URL로 Blob 재생성)
async function restoreMissingFile(video) {
  if (!video || video.file instanceof File) return;
  const src = video.displayUrl || video.originUrl;
  if (!src) return;
  try {
    const resp = await fetch(src);
    const blob = await resp.blob();
    // 파일명 추론: name/title/기본값
    const filename = (video.name || video.title || 'video') + (blob.type && !blob.type.includes('mp4') ? '' : '.mp4');
    video.file = new File([blob], filename, { type: blob.type || 'video/mp4' });
  } catch (e) {
    console.warn('Failed to restore File from URL', e);
  }
}

async function restoreAllMissingFiles() {
  const targets = videoFiles.value.filter(v => !(v.file instanceof File) && (v.displayUrl || v.originUrl));
  for (const v of targets) {
    await restoreMissingFile(v);
  }
}

// Pinia 스토어에서 동영상 목록을 불러와서 Summary 메뉴의 로컬 배열에 복사
onMounted(() => {
  if (Array.isArray(summaryVideoStore.videos) && summaryVideoStore.videos.length > 0) {
    // Summary 전용 표시 URL을 분리하여 Video Storage 원본 URL(ObjectURL)과 독립
    videoFiles.value = summaryVideoStore.videos.map(v => {
      const hasFile = v.file instanceof File;
      const summaryObjectUrl = hasFile ? URL.createObjectURL(v.file) : null; // Summary에서 새로 만든 URL
      return {
        id: v.id,
        name: v.name ?? v.title,
        originUrl: v.url || '', // Video Storage에서 넘어온 원본 URL (삭제 시 revoke 금지)
        displayUrl: summaryObjectUrl || v.url || '', // 렌더링에 사용할 URL
        summaryObjectUrl, // Summary가 관리/해제할 URL (없으면 null)
        date: v.date ?? '',
        summary: v.summary ?? '',
        file: hasFile ? v.file : null
      };
    });
    selectedIndexes.value = videoFiles.value.map(v => v.id);
    zoomedIndex.value = videoFiles.value.length > 0 ? 0 : null;
    // 초기 로딩 후 File 객체가 null인 항목 복원 시도 (세션 재진입, localStorage 경유 케이스)
    restoreAllMissingFiles();
  }
});

// Summary 페이지에서 벗어날 때 영상 URL 및 스토어 정리 (다시 들어왔을 때 이전 영상이 남지 않도록)
onUnmounted(() => {
  // Summary에서 만든 전용 ObjectURL만 해제 (원본은 유지)
  videoFiles.value.forEach(v => {
    if (v.summaryObjectUrl) {
      try { URL.revokeObjectURL(v.summaryObjectUrl); } catch (_) { }
    }
  });
  summaryVideoStore.clearVideos();
  videoFiles.value = [];
  selectedIndexes.value = [];
  zoomedIndex.value = null;
});

// watch 제거: 매 변경마다 새 ObjectURL 생성되어 누수 가능성 감소

function onDragOver(e) {
  isDragging.value = true;
}
function onDragLeave(e) {
  isDragging.value = false;
}
function onDrop(e) {
  isDragging.value = false;
  const files = e.dataTransfer.files;
  if (files && files.length > 0) {
    const file = files[0];
    if (file.type.startsWith('video/')) {
      const summaryObjectUrl = URL.createObjectURL(file);
      videoFiles.value.push({
        id: Date.now() + Math.random(),
        name: file.name,
        originUrl: '', // 드롭 업로드는 Video Storage와 무관한 직접 업로드
        displayUrl: summaryObjectUrl,
        summaryObjectUrl,
        date: new Date().toISOString().slice(0, 10),
        summary: '',
        file
      });
    }
  }
  if (videoFiles.value.length > 0 && selectedIndexes.value.length === 0) {
    selectedIndexes.value = videoFiles.value.map(v => v.id);
  }
}

function onVideoAreaClick() {
  if (fileInputRef.value) {
    fileInputRef.value.click();
  }
}

function selectVideo(id) {
  const idx = selectedIndexes.value.indexOf(id);
  if (idx === -1) {
    selectedIndexes.value.push(id);
  } else {
    selectedIndexes.value.splice(idx, 1);
  }
}

function zoomVideo(idx) {
  isZoomed.value = true;
  zoomedIndex.value = idx;
}

function unzoomVideo() {
  isZoomed.value = false;
  zoomedIndex.value = null;
}

function onUpload(e) {
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
      const summaryObjectUrl = URL.createObjectURL(file);
      return {
        id: Date.now() + Math.random(),
        name: file.name,
        originUrl: '',
        displayUrl: summaryObjectUrl,
        summaryObjectUrl,
        date: new Date().toISOString().slice(0, 10),
        summary: "",
        file
      };
    });
  videoFiles.value.unshift(...newVideos);
  // input[type=file] value 초기화 (동일 파일 재업로드 가능)
  if (fileInputRef.value) fileInputRef.value.value = '';
  if (videoFiles.value.length > 0 && selectedIndexes.value.length === 0) {
    selectedIndexes.value = videoFiles.value.map(v => v.id);
  }
}

async function runInference() {
  const VSS_API_URL = 'http://localhost:8001/vss-summarize';

  // 선택된 비디오 우선 사용, 없으면 첫 번째
  const firstSelectedId = selectedIndexes.value[0];
  let videoObj = videoFiles.value.find(v => v.id === firstSelectedId) || videoFiles.value[0];

  // File 복원 시도
  if (videoObj && !(videoObj.file instanceof File)) {
    await restoreMissingFile(videoObj);
  }
  if (!videoObj || !(videoObj.file instanceof File)) {
    alert('선택된(또는 첫 번째) 동영상의 File 객체를 확보하지 못했습니다. 다시 업로드 후 시도하세요.');
    return;
  }

  // NaN 방지용 헬퍼
  const safeNum = (val, fallback) => {
    const n = Number(val);
    return Number.isFinite(n) ? n : fallback;
  };

  const formData = new FormData();
  formData.append('file', videoObj.file);
  formData.append('prompt', prompt.value ?? '');
  formData.append('csprompt', settingStore.captionPrompt ?? '');
  formData.append('saprompt', settingStore.aggregationPrompt ?? '');
  formData.append('chunk_duration', safeNum(settingStore.chunk, 10));
  formData.append('model', (settingStore.model && String(settingStore.model)) || 'default');
  formData.append('num_frames_per_chunk', safeNum(settingStore.nfmc, 1));
  formData.append('frame_width', safeNum(settingStore.frameWidth, 224));
  formData.append('frame_height', safeNum(settingStore.frameHeight, 224));
  formData.append('top_k', safeNum(settingStore.topk, 1));
  formData.append('top_p', safeNum(settingStore.topp, 1.0));
  formData.append('temperature', safeNum(settingStore.temp, 1.0));
  formData.append('max_tokens', safeNum(settingStore.maxTokens, 512));
  formData.append('seed', safeNum(settingStore.seed, 1));
  formData.append('batch_size', safeNum(settingStore.batch, 6));
  formData.append('rag_batch_size', safeNum(settingStore.RAG_batch, 1));
  formData.append('rag_top_k', safeNum(settingStore.RAG_topk, 1));
  formData.append('summary_top_p', safeNum(settingStore.S_TopP, 1.0));
  formData.append('summary_temperature', safeNum(settingStore.S_TEMPERATURE, 1.0));
  formData.append('summary_max_tokens', safeNum(settingStore.SMAX_TOKENS, 512));
  formData.append('chat_top_p', safeNum(settingStore.C_TopP, 1.0));
  formData.append('chat_temperature', safeNum(settingStore.C_TEMPERATURE, 1.0));
  formData.append('chat_max_tokens', safeNum(settingStore.C_MAX_TOKENS, 512));
  formData.append('alert_top_p', safeNum(settingStore.A_TopP, 1.0));
  formData.append('alert_temperature', safeNum(settingStore.A_TEMPERATURE, 1.0));
  formData.append('alert_max_tokens', safeNum(settingStore.A_MAX_TOKENS, 512));

  // 로딩 메시지 삽입 (성공 시 제거 예정)
  const loadingId = Date.now() + Math.random();
  chatMessages.value.push({ id: loadingId, role: 'system', content: '⏳ Summarization 요청 전송 중...' });
  const startTime = Date.now();
  try {
    const res = await fetch(VSS_API_URL, { method: 'POST', body: formData });
    const endTime = Date.now();
    const elapsed = ((endTime - startTime) / 1000).toFixed(2);
    if (!res.ok) {
      // FastAPI 422 등의 상세 오류 본문 표시
      let errText = await res.text();
      const errHtml = `❌ 요청 실패 (HTTP ${res.status})<br><code>${errText}</code><br><br>추론 시간: ${elapsed} seconds`;
      response.value = errHtml;
      chatMessages.value.push({ id: Date.now() + Math.random(), role: 'system', content: errHtml });
      console.error('Summarization error response:', errText);
      return;
    }
    const data = await res.json();
    const videoId = data.video_id;
    summarizedVideoId.value = videoId; // 전역 저장
    const markedsummary = marked.parse(data.summary || '');
    const summaryHtml = `<div class='font-semibold'>✅ Summarization Completed</div><br>${markedsummary}<br><br><div class='text-xs text-gray-500'>추론 시간: ${elapsed} s</div>`;
    response.value = summaryHtml; // 저장용
    // 로딩 메시지 제거 (성공 시)
    const loadingIdx = chatMessages.value.findIndex(m => m.id === loadingId);
    if (loadingIdx !== -1) chatMessages.value.splice(loadingIdx, 1);
    chatMessages.value.push({ id: Date.now() + Math.random(), role: 'assistant', content: summaryHtml });
  } catch (e) {
    const endTime = Date.now();
    const elapsed = ((endTime - startTime) / 1000).toFixed(2);
    const errHtml = `❌ 네트워크/예외 오류: ${(e && e.message) || 'unknown'}<br><br>추론 시간: ${elapsed} seconds`;
    response.value = errHtml;
    chatMessages.value.push({ id: Date.now() + Math.random(), role: 'system', content: errHtml });
    console.error('Summarization request failed:', e);
  }
}

// 동영상이 1개일 때 삭제
function removeSingleVideo() {
  if (videoFiles.value.length === 1) {
    const target = videoFiles.value[0];
    if (target.summaryObjectUrl) {
      try { URL.revokeObjectURL(target.summaryObjectUrl); } catch (_) { }
    }
    // 재생 중 목록 정리
    const playIdx = playingVideoIds.value.indexOf(target.id);
    if (playIdx !== -1) playingVideoIds.value.splice(playIdx, 1);
    videoFiles.value = [];
    selectedIndexes.value = [];
    isZoomed.value = false;
    zoomedIndex.value = null;
    // 재생 상태 및 레퍼런스 초기화
    hoveredVideoId.value = null;
    playingVideoIds.value = [];
    videoRefs.value = {};
    // 프롬프트 텍스트 초기화
    prompt.value = "";
    // 요약 결과도 초기화
    response.value = '';
    chatMessages.value = [];
    // 스토어도 즉시 비움 (다시 방문 시 재로드 방지)
    if (summaryVideoStore && typeof summaryVideoStore.clearVideos === 'function') {
      summaryVideoStore.clearVideos();
    } else if (summaryVideoStore && typeof summaryVideoStore.setVideos === 'function') {
      summaryVideoStore.setVideos([]);
    }
  }
}

function batchRemoveSelectedVideos() {
  videoFiles.value
    .filter(v => selectedIndexes.value.includes(v.id))
    .forEach(v => {
      if (v.summaryObjectUrl) {
        try { URL.revokeObjectURL(v.summaryObjectUrl); } catch (_) { }
      }
      const playIdx = playingVideoIds.value.indexOf(v.id);
      if (playIdx !== -1) playingVideoIds.value.splice(playIdx, 1);
      // 개별 videoRefs 제거
      if (videoRefs.value[v.id]) delete videoRefs.value[v.id];
    });
  videoFiles.value = videoFiles.value.filter(v => !selectedIndexes.value.includes(v.id));
  selectedIndexes.value = [];
  // 프롬프트 텍스트 항상 초기화 (부분 삭제도 포함)
  prompt.value = "";
  // 요약 결과도 초기화 (부분 삭제 포함 전체 삭제 시 동일하게 초기화)
  response.value = '';
  chatMessages.value = [];
  if (videoFiles.value.length === 0) {
    isZoomed.value = false;
    zoomedIndex.value = null;
    hoveredVideoId.value = null;
    playingVideoIds.value = [];
    videoRefs.value = {};
    if (summaryVideoStore && typeof summaryVideoStore.clearVideos === 'function') {
      summaryVideoStore.clearVideos();
    } else if (summaryVideoStore && typeof summaryVideoStore.setVideos === 'function') {
      summaryVideoStore.setVideos([]);
    }
  }
}

async function onAsk(q) {
  const VSS_API_URL = 'http://localhost:8001/vss-query';
  const formData = new FormData();

  const safeNum = (val, fallback) => {
    const n = Number(val);
    return Number.isFinite(n) ? n : fallback;
  };

  const firstSelectedId = selectedIndexes.value[0];
  let videoObj = videoFiles.value.find(v => v.id === firstSelectedId) || videoFiles.value[0];

  if (summarizedVideoId.value) {
    // 요약된 비디오 ID가 있으면 그것을 우선 사용
    formData.append('video_id', summarizedVideoId.value);
  }
  else {
    // File 복원 시도
    if (videoObj && !(videoObj.file instanceof File)) {
      await restoreMissingFile(videoObj);
    }
    if (!videoObj || !(videoObj.file instanceof File)) {
      alert('선택된(또는 첫 번째) 동영상의 File 객체를 확보하지 못했습니다. 다시 업로드 후 시도하세요.');
      return;
    }
    formData.append('file', videoObj.file);
  }
  formData.append('query', ask_prompt.value ?? '');
  formData.append('chunk_size', safeNum(settingStore.chunk, 10));
  formData.append('top_k', safeNum(settingStore.topk, 1));
  formData.append('top_p', safeNum(settingStore.topp, 1.0));
  formData.append('temperature', safeNum(settingStore.temp, 1.0));
  formData.append('max_new_tokens', safeNum(settingStore.maxTokens, 512));
  formData.append('seed', safeNum(settingStore.seed, 1));

  // 사용자가 입력한 질문을 채팅창에 추가
  chatMessages.value.push({ id: Date.now() + Math.random(), role: 'user', content: q });

  const res = await fetch(VSS_API_URL, { method: 'POST', body: formData });
  if (!res.ok) {
    alert(`질의 요청 실패 (HTTP ${res.status})`);
    return;
  }
  const data = await res.json();
  const markedanswer = marked.parse(data.summary || '');
  const answerHtml = `<div class='font-semibold'>✅ Query Answered</div><br>${markedanswer}`;
  chatMessages.value.push({ id: Date.now() + Math.random(), role: 'assistant', content: answerHtml });

}

function clear() {
  prompt.value = "";
  response.value = "";
  chatMessages.value = [];
}

function togglePlay(videoId) {
  const el = videoRefs.value[videoId];
  if (!el) {
    // 삭제 후 남은 stale id 정리
    const ghostIdx = playingVideoIds.value.indexOf(videoId);
    if (ghostIdx !== -1) playingVideoIds.value.splice(ghostIdx, 1);
    return;
  }
  // 다중 재생 허용: 기존 재생 중인 다른 비디오를 중지하지 않음
  // playingVideoIds 배열은 재생 중인 모든 비디오 id를 유지
  const idx = playingVideoIds.value.indexOf(videoId);
  if (idx === -1) {
    el.play();
    playingVideoIds.value.push(videoId);
  } else {
    el.pause();
    playingVideoIds.value.splice(idx, 1);
  }
}

function onVideoEnded(videoId) {
  const idx = playingVideoIds.value.indexOf(videoId);
  if (idx !== -1) playingVideoIds.value.splice(idx, 1);
}

function removeVideo() {
  videoFile.value = null;
  videoUrl.value = "";
}
</script>

<style scoped>
.bubble {
  max-width: 70%;
  padding: 10px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
}

.bubble-user {
  background-color: #ffffff;
  /* 흰색 배경 */
  color: #000000;
  /* 검정 텍스트 */
  text-align: right;
  /* 텍스트 오른쪽 정렬 */
  align-self: flex-end;
  /* 채팅창 오른쪽에 배치 */
  box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);
  /* 그림자 추가 */
}

.bubble-assistant {
  background-color: #f1f1f1;
  /* 회색 배경 */
  color: #333333;
  /* 어두운 텍스트 */
  text-align: left;
  /* 텍스트 왼쪽 정렬 */
  align-self: flex-start;
  /* 채팅창 왼쪽에 배치 */
}

.bubble-system {
  background-color: #e0e0e0;
  /* 시스템 메시지 배경 */
  color: #666666;
  /* 시스템 메시지 텍스트 */
  text-align: center;
  /* 텍스트 가운데 정렬 */
}

.brightness-75 {
  filter: brightness(75%);
  transition: filter 0.3s ease;
}

.transition-all {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
</style>
