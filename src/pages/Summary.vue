<template>
  <div class="grid lg:grid-cols-2 gap-6">
    <!-- 좌측: 비디오/업로드 -->
    <section class="rounded-2xl border p-4 bg-gray-50">
      <h2 class="font-semibold mb-3">
        {{ videoFile && videoFile.name ? videoFile.name : 'Video Section' }}
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
          <video class="w-full h-full rounded-xl" :src="videoFiles[0].url" controls></video>
        </template>
        <template v-else>
          <!-- 여러 개일 때 리스트 또는 확대 -->
          <div v-if="!isZoomed" id="list" class="w-full h-full bg-gray-300 rounded-[12px] p-6">
            <div class="w-[100%] h-[100%] border-[1px] border-black bg-white rounded-[12px]">
              <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6 p-6">
                <div v-for="(video, idx) in videoFiles" :key="video.id"
                  class="flex flex-col items-center justify-center bg-gray-100 rounded-lg shadow hover:bg-blue-100 cursor-pointer p-3 border border-gray-300"
                  @click="selectVideo(idx)">
                  <div class="w-[100%] h-[100%] flex items-center justify-center bg-gray-300 rounded mb-2 overflow-hidden relative">
                    <input type="checkbox" class="absolute top-1 left-1 z-10" :checked="selectedIndexes.includes(idx)" @change.stop="selectVideo(idx)" />
                    <video v-if="video.url" :src="video.url" class="object-cover rounded" controls preload="metadata"></video>
                    <span v-else class="text-gray-400">No Thumbnail</span>
                    <div v-if="video.title || video.name" class="absolute bottom-0 left-0 w-full bg-black bg-opacity-60 text-white text-xs px-1 py-0.5 truncate text-center pointer-events-none">
                      {{ video.title || video.name }}
                    </div>
                  </div>
                  <div class="flex gap-2 mt-1">
                    <button @click.stop="zoomVideo(idx)" class="text-blue-500 hover:underline text-xs">열기</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="flex flex-col items-center w-full">
            <div class="relative w-full h-[100%] mb-2">
              <video v-if="videoFiles[zoomedIndex]" :src="videoFiles[zoomedIndex].url" class="w-full h-[100%] rounded-xl" controls></video>
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
          :disabled="videoFiles.length === 0 || selectedIndex === null">
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
// 동영상이 1개일 때 삭제
function removeSingleVideo() {
  if (videoFiles.value.length === 1) {
    if (videoUrls.value[0]) {
      try { URL.revokeObjectURL(videoUrls.value[0]); } catch (e) { }
    }
    videoFiles.value.splice(0, 1);
    videoUrls.value.splice(0, 1);
    selectedIndexes.value = [];
    isZoomed.value = false;
    zoomedIndex.value = null;
  }
}
import { ref, inject, onMounted, watch, computed } from "vue";
import PromptInput from "@/components/PromptInput.vue";
import api from "@/services/api";
import { useSettingStore } from '@/stores/settingStore';
import { useSummaryVideoStore } from '@/stores/summaryVideoStore';
import { marked } from 'marked';

const summaryParams = inject("summaryParams"); // Setting.vue에서 제공한 파라미터

const videoFiles = ref([]); // 여러 동영상 파일
const videoUrls = ref([]); // 각 동영상 미리보기 URL
// videoFiles가 변경될 때마다 videoUrls도 자동 갱신
watch(videoFiles, (newFiles) => {
  videoUrls.value = newFiles.map(f => f.url ? f.url : (f instanceof File ? URL.createObjectURL(f) : ''));
});
const summaryVideoStore = useSummaryVideoStore();
onMounted(() => {
  // Pinia 스토어에서 선택된 동영상 객체를 불러옴
  if (summaryVideoStore.videos && Array.isArray(summaryVideoStore.videos) && summaryVideoStore.videos.length > 0) {
    videoFiles.value = [...summaryVideoStore.videos];
    videoUrls.value = videoFiles.value.map(v => v.url);
    selectedIndex.value = 0;
    zoomedIndex.value = videoFiles.value.length > 0 ? 0 : null;
    summaryVideoStore.clearVideos();
  }
});
const selectedIndexes = ref([]); // 선택된 동영상 인덱스 배열
const prompt = ref("");
const response = ref("");
const isDragging = ref(false);
const fileInputRef = ref(null);

function onVideoAreaClick() {
  if (!videoUrl.value && fileInputRef.value) {
    fileInputRef.value.click();
  }
}

function onUpload(e) {
  const files = Array.from(e.target.files ?? []);
  if (!files.length) return;
  for (const file of files) {
    if (!file.type.startsWith('video/')) {
      alert('동영상 파일만 업로드할 수 있습니다.');
      continue;
    }
    const url = URL.createObjectURL(file);
    const video = {
      id: Date.now() + Math.random(),
      name: file.name,
      url,
      date: new Date().toISOString().slice(0, 10),
      summary: "",
      file // File 객체도 함께 저장
    };
    videoFiles.value.unshift(video);
    videoUrls.value.unshift(url);
  }
  // input[type=file] value 초기화 (동일 파일 재업로드 가능)
  if (fileInputRef.value) fileInputRef.value.value = '';
  if (videoFiles.value.length > 0 && selectedIndex.value === null) {
    selectedIndex.value = 0;
  }
}

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
      videoFile.value = file;
      videoUrl.value = URL.createObjectURL(file);
    } else {
      alert('동영상 파일만 업로드할 수 있습니다.');
    }
  }
  if (videoFiles.value.length > 0 && selectedIndex.value === null) {
    selectedIndex.value = 0;
  }
}

function selectVideo(idx) {
  if (selectedIndexes.value.includes(idx)) {
    selectedIndexes.value = selectedIndexes.value.filter(i => i !== idx);
  } else {
    selectedIndexes.value.push(idx);
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

function batchRemoveSelectedVideos() {
  const sorted = [...selectedIndexes.value].sort((a, b) => b - a);
  for (const idx of sorted) {
    if (videoUrls.value[idx]) {
      try { URL.revokeObjectURL(videoUrls.value[idx]); } catch (e) { }
    }
    videoFiles.value.splice(idx, 1);
    videoUrls.value.splice(idx, 1);
  }
  selectedIndexes.value = [];
  if (videoFiles.value.length === 0) {
    isZoomed.value = false;
    zoomedIndex.value = null;
  }
}


async function runInference() {
  const VSS_API_URL = 'http://localhost:8001/vss-summarize'
  if (videoFiles.value.length === 0) return;
  // 여러 파일을 서버에 업로드
  const formData = new FormData();
  formData.append('file', videoFiles.value[0].file)
  formData.append('prompt', prompt.value)
  formData.append('csprompt', settingStore.captionPrompt)
  formData.append('saprompt', settingStore.aggregationPrompt)
  formData.append('chunk_duration', settingStore.chunk)
  formData.append('model', "")
  formData.append('num_frames_per_chunk', settingStore.nfmc)
  formData.append('frame_width', settingStore.frameWidth)
  formData.append('frame_height', settingStore.frameHeight)
  formData.append('top_k', settingStore.topk)
  formData.append('top_p', settingStore.topp)
  formData.append('temperature', settingStore.temp)
  formData.append('max_tokens', settingStore.maxTokens)
  formData.append('seed', settingStore.seed)
  formData.append('batch_size', settingStore.batch)
  formData.append('rag_batch_size', settingStore.RAG_batch)
  formData.append('rag_top_k', settingStore.RAG_topk)
  formData.append('summary_top_p', settingStore.S_TopP)
  formData.append('summary_temperature', settingStore.S_TEMPERATURE)
  formData.append('summary_max_tokens', settingStore.SMAX_TOKENS)
  formData.append('chat_top_p', settingStore.C_TopP)
  formData.append('chat_temperature', settingStore.C_TEMPERATURE)
  formData.append('chat_max_tokens', settingStore.C_MAX_TOKENS)
  formData.append('alert_top_p', settingStore.A_TopP)
  formData.append('alert_temperature', settingStore.A_TEMPERATURE)
  formData.append('alert_max_tokens', settingStore.A_MAX_TOKENS)


  response.value = '⏳ Sending video + prompt to backend for summarization...'
  const startTime = Date.now();
  try {
    const res = await fetch(VSS_API_URL, { method: 'POST', body: formData })
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

async function onAsk(q) {
  const res = await api.askAboutResult({ question: q, context: response.value });
  response.value += `\n\nQ: ${q}\nA: ${res.answer}`;
}

function saveResult() {
  api.saveSummary({ content: response.value });
  // 썸네일/메타데이터를 localStorage에 저장
  if (videoFile.value && videoUrl.value) {
    const saved = JSON.parse(localStorage.getItem('vss_videos') || '[]');
    const newItem = {
      id: Date.now(),
      title: videoFile.value.name,
      date: new Date().toISOString().slice(0, 10),
      url: videoUrls.value[selectedIndex.value],
      summary: response.value
    };
    saved.unshift(newItem);
    localStorage.setItem('vss_videos', JSON.stringify(saved));
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
