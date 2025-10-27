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
        @dragover.prevent="onDragOver"
        @dragleave.prevent="onDragLeave"
        @drop.prevent="onDrop"
        @click="onVideoAreaClick"
      >
        <template v-if="!videoUrl">
          <span v-if="!isDragging">
            <span class="font-bold text-blue-500 flex flex-col items-center justify-center text-center w-full">
              Drop Video here<br>-- or --<br>Click to upload
            </span>
          </span>
          <span v-else class="text-blue-600 font-bold">여기에 파일을 놓으세요</span>
        </template>
        <video v-else class="w-full h-full rounded-xl" :src="videoUrl" controls></video>
      </div>



      <!-- 프롬프트 입력 블럭 -->
      <div class="mb-3">
        <input
          v-model="prompt"
          type="text"
          class="w-full border rounded-md px-3 py-2 mt-2"
          placeholder="프롬프트를 입력하세요."
        />
      </div>

      <div class="flex items-center gap-3">
        <input type="file" accept="video/*" @change="onUpload" ref="fileInputRef" class="hidden" />
        <button class="px-4 py-2 rounded-md bg-vix-primary text-white" @click="runInference" :disabled="!videoFile">
          추론 실행
        </button>
      </div>

      <div v-if="videoUrl" class="mt-2 flex">
        <button class="px-3 py-2 rounded-md bg-red-500 text-white hover:bg-red-600 transition" @click="removeVideo">
          동영상 제거
        </button>
      </div>

      <p class="text-xs text-gray-500 mt-2">
        Chunk 크기/프롬프트 등 세부 설정은 Setting에서 조정하세요.
      </p>
    </section>

    <!-- 우측: 결과/프롬프트 -->
    <section class="rounded-2xl border p-4">
      <h2 class="font-semibold mb-3">요약 결과</h2>

      <div class="h-72 border rounded-xl p-3 bg-gray-50 overflow-auto whitespace-pre-wrap text-sm">
        {{ result || "추론 결과가 여기에 표시됩니다." }}
      </div>

      <div class="mt-4">
        <PromptInput
          v-model="prompt"
          placeholder="typing ask here..."
          @ask="onAsk" />
      </div>

      <div class="mt-3 flex gap-2">
        <button class="px-3 py-2 rounded-md bg-gray-100" @click="saveResult">결과 저장</button>
        <button class="px-3 py-2 rounded-md bg-gray-100" @click="clear">초기화</button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from "vue";
import PromptInput from "@/components/PromptInput.vue";
import api from "@/services/api";

const videoFile = ref(null);
const videoUrl = ref("");
const prompt = ref("");
const result = ref("");
const isDragging = ref(false);
const fileInputRef = ref(null);
function onVideoAreaClick() {
  // 동영상이 이미 업로드된 경우에는 클릭 시 업로드창 열지 않음
  if (!videoUrl.value && fileInputRef.value) {
    fileInputRef.value.click();
  }
}

function onUpload(e) {
  videoFile.value = e.target.files?.[0] ?? null;
  if (videoFile.value) {
    videoUrl.value = URL.createObjectURL(videoFile.value);
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
}

async function runInference() {
  if (!videoFile.value) return;
  const res = await api.runVssInference({ fileName: videoFile.value.name });
  result.value = res.summary;
}

async function onAsk(q) {
  const res = await api.askAboutResult({ question: q, context: result.value });
  result.value += `\n\nQ: ${q}\nA: ${res.answer}`;
}

function saveResult() {
  api.saveSummary({ content: result.value });
  alert("요약 결과를 저장했습니다.");
}

function clear() {
  prompt.value = "";
  result.value = "";
}

function removeVideo() {
  videoFile.value = null;
  videoUrl.value = "";
}
</script>
