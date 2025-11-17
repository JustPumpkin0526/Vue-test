<template>
  <div class="grid lg:grid-cols-2 gap-6">
    <!-- 좌측: 비디오/업로드 -->
    <section class="rounded-2xl border p-4 bg-gray-50">
      <h2 class="font-semibold mb-3">
        {{ selectedIndexes.length === 0 ? 'Video Section' : (videoFiles.find(v => v.id === selectedIndexes[0])?.name || 'Video Section') }}
      </h2>


      <div
        class="aspect-video h-92 rounded-xl mb-3 flex items-center justify-center text-gray-600 transition border-2 cursor-pointer"
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
          <video class="w-full h-full rounded-xl" :src="videoFiles[0].displayUrl" controls></video>
        </template>
        <template v-else>
          <!-- 여러 개일 때 리스트 또는 확대 -->
          <div v-if="!isZoomed" id="list" class="w-full bg-gray-300 rounded-[12px] p-6">
            <div class="w-full border-[1px] border-black bg-white rounded-[12px] overflow-y-auto" style="height:600px; min-height:600px; max-height:600px;">
              <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-3 gap-6 p-6">
                <div v-for="(video, idx) in videoFiles" :key="video.id"
                  class="flex flex-col items-center justify-center bg-gray-100 rounded-lg shadow hover:bg-blue-100 cursor-pointer p-3 border border-gray-300"
                  @click="selectVideo(video.id)">
                  <div class="w-[100%] h-[100%] flex items-center justify-center bg-gray-300 rounded mb-2 overflow-hidden relative">
                    <input type="checkbox" class="absolute top-1 left-1 z-10" v-model="selectedIndexes" :value="video.id" />
                    <video v-if="video.displayUrl" :src="video.displayUrl" class="object-cover rounded" controls preload="metadata"></video>
                    <span v-else class="text-gray-400">No Thumbnail</span>
                    <div v-if="video.title || video.name"
                      class="absolute top-1 right-1 bg-black bg-opacity-60 text-white text-xs px-2 py-1 rounded truncate max-w-[70%] pointer-events-none">
                      {{ video.title || video.name }}
                    </div>
                  </div>
                  <div class="flex gap-2 mt-1">
                    <button
                      @click.stop="zoomVideo(idx)"
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
              <video v-if="videoFiles[zoomedIndex]" :src="videoFiles[zoomedIndex].displayUrl" class="w-full h-[100%] rounded-xl" controls></video>
              <div v-if="videoFiles[zoomedIndex]" class="absolute top-2 left-2 bg-gray-300 text-black text-xs px-2 py-1 rounded truncate max-w-[70%] pointer-events-none">
                {{ videoFiles[zoomedIndex].name || videoFiles[zoomedIndex].title }}
              </div>
            </div>
            <button class="px-3 py-2 rounded-md bg-gray-300 text-black mb-2" @click="unzoomVideo">되돌아가기</button>
          </div>
        </template>
      </div>



      <!-- 프롬프트 입력 블럭 -->
      <div class="mb-3">
        <input v-model="prompt" type="text" class="w-full border rounded-md px-3 py-2 mt-2"
          placeholder="프롬프트를 입력하세요." />
      </div>

      <div class="flex items-center gap-3">
        <input type="file" accept="video/*" multiple @change="onUpload" ref="fileInputRef" class="hidden"
          :disabled="videoFiles.length > 0" />
        <button class="px-4 py-2 rounded-md bg-vix-primary text-white" @click="runInference"
          :disabled="videoFiles.length === 0 || selectedIndexes.length === 0">
          추론 실행
        </button>
      </div>

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
    <section class="rounded-2xl border p-4">
      <h2 class="font-semibold mb-3">요약 결과</h2>

      <div class="prose w-full max-w-none h-[600px] border rounded-xl p-3 bg-gray-50 overflow-auto text-base"
        v-html="response">
      </div>

      <div class="mt-4">
        <PromptInput v-model="prompt" placeholder="typing ask here..." @ask="onAsk" />
      </div>

      <div class="mt-3 flex gap-2">
        <button class="px-3 py-2 rounded-md bg-gray-100" @click="saveResult">결과 저장</button>
        <button class="px-3 py-2 rounded-md bg-gray-100" @click="clear">초기화</button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { useSummaryVideoStore } from '@/stores/summaryVideoStore';
import PromptInput from "@/components/PromptInput.vue";
import api from "@/services/api";
import { useSettingStore } from '@/stores/settingStore';
import { marked } from 'marked';

const selectedIndexes = ref([]); // 선택된 동영상 id 배열
const prompt = ref("");
const response = ref("");
const isDragging = ref(false);
const fileInputRef = ref(null);
const ask_prompt = ref("");
const isZoomed = ref(false); // 확대 여부
const zoomedIndex = ref(null); // 확대된 동영상 인덱스
const settingStore = useSettingStore();
const videoFiles = ref([]); // Summary 메뉴의 로컬 동영상 배열
// videoUrls 제거: 템플릿에서 사용되지 않아 메모리 관리 단순화
const summaryVideoStore = useSummaryVideoStore();

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
      try { URL.revokeObjectURL(v.summaryObjectUrl); } catch (_) {}
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
  // videoFiles[0].file이 File 객체인지 체크
  const videoObj = videoFiles.value[0];
  // 필요 시 즉석 복원 시도
  if (videoObj && !(videoObj.file instanceof File)) {
    await restoreMissingFile(videoObj);
  }
  if (!videoObj || !(videoObj.file instanceof File)) {
    alert('업로드할 동영상 파일이 올바르지 않습니다. 새로 업로드한 후 다시 시도해주세요.');
    return;
  }
  const formData = new FormData();
  formData.append('file', videoObj.file);
  formData.append('prompt', prompt.value ?? "");
  formData.append('csprompt', settingStore.captionPrompt ?? "");
  formData.append('saprompt', settingStore.aggregationPrompt ?? "");
  formData.append('chunk_duration', Number(settingStore.chunk) ?? 10);
  formData.append('model', "");
  formData.append('num_frames_per_chunk', Number(settingStore.nfmc) ?? 1);
  formData.append('frame_width', Number(settingStore.frameWidth) ?? 224);
  formData.append('frame_height', Number(settingStore.frameHeight) ?? 224);
  formData.append('top_k', Number(settingStore.topk) ?? 1);
  formData.append('top_p', Number(settingStore.topp) ?? 1.0);
  formData.append('temperature', Number(settingStore.temp) ?? 1.0);
  formData.append('max_tokens', Number(settingStore.maxTokens) ?? 512);
  formData.append('seed', Number(settingStore.seed) ?? 42);
  formData.append('batch_size', Number(settingStore.batch) ?? 1);
  formData.append('rag_batch_size', Number(settingStore.RAG_batch) ?? 1);
  formData.append('rag_top_k', Number(settingStore.RAG_topk) ?? 1);
  formData.append('summary_top_p', Number(settingStore.S_TopP) ?? 1.0);
  formData.append('summary_temperature', Number(settingStore.S_TEMPERATURE) ?? 1.0);
  formData.append('summary_max_tokens', Number(settingStore.SMAX_TOKENS) ?? 512);
  formData.append('chat_top_p', Number(settingStore.C_TopP) ?? 1.0);
  formData.append('chat_temperature', Number(settingStore.C_TEMPERATURE) ?? 1.0);
  formData.append('chat_max_tokens', Number(settingStore.C_MAX_TOKENS) ?? 512);
  formData.append('alert_top_p', Number(settingStore.A_TopP) ?? 1.0);
  formData.append('alert_temperature', Number(settingStore.A_TEMPERATURE) ?? 1.0);
  formData.append('alert_max_tokens', Number(settingStore.A_MAX_TOKENS) ?? 512);

  response.value = '⏳ Sending video + prompt to backend for summarization...';
  const startTime = Date.now();
  try {
    const res = await fetch(VSS_API_URL, { method: 'POST', body: formData });
    const data = await res.json();
    const endTime = Date.now();
    const elapsed = ((endTime - startTime) / 1000).toFixed(2);
    const markedsummary = marked.parse(data.summary || '');
    response.value = `<div>✅ Summarization Completed!</div><br><br>${markedsummary}<br><br><div>추론 시간: ${elapsed} seconds</div>`;
  } catch {
    const endTime = Date.now();
    const elapsed = ((endTime - startTime) / 1000).toFixed(2);
    response.value = `❌ Failed to send video. Please check server.\n\n추론 시간: ${elapsed} seconds`;
  }
}

// 동영상이 1개일 때 삭제
function removeSingleVideo() {
  if (videoFiles.value.length === 1) {
    const target = videoFiles.value[0];
    if (target.summaryObjectUrl) {
      try { URL.revokeObjectURL(target.summaryObjectUrl); } catch (_) { }
    }
    videoFiles.value = [];
    selectedIndexes.value = [];
    isZoomed.value = false;
    zoomedIndex.value = null;
  }
}

function batchRemoveSelectedVideos() {
  videoFiles.value
    .filter(v => selectedIndexes.value.includes(v.id))
    .forEach(v => {
      if (v.summaryObjectUrl) {
        try { URL.revokeObjectURL(v.summaryObjectUrl); } catch (_) {}
      }
    });
  videoFiles.value = videoFiles.value.filter(v => !selectedIndexes.value.includes(v.id));
  selectedIndexes.value = [];
  if (videoFiles.value.length === 0) {
    isZoomed.value = false;
    zoomedIndex.value = null;
  }
}

async function onAsk(q) {
  const res = await api.askAboutResult({ question: q, context: response.value });
  response.value += `\n\nQ: ${q}\nA: ${res.answer}`;

  api.saveSummary({ content: response.value });
  // 썸네일/메타데이터를 localStorage에 저장
  if (selectedIndexes.value.length > 0) {
    const firstId = selectedIndexes.value[0];
    const video = videoFiles.value.find(v => v.id === firstId);
    if (video) {
      const saved = JSON.parse(localStorage.getItem('vss_videos') || '[]');
      const newItem = {
        id: Date.now(),
        title: video.name,
        date: new Date().toISOString().slice(0, 10),
        url: video.originUrl || video.displayUrl, // 저장 시 원본 우선
        summary: response.value
      };
      saved.unshift(newItem);
      localStorage.setItem('vss_videos', JSON.stringify(saved));
    }
  }
  alert("요약 결과를 저장했습니다.");
}

function clear() {
  prompt.value = "";
  response.value = "";
}

function removeVideo() {
  videoFile.value = null;
  videoUrl.value = "";
}
</script>
