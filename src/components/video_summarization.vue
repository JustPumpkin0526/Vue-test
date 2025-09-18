<template>
  <div class="min-h-screen bg-[#F5F5F5] flex justify-start items-start p-4">
    <!-- Left Panel -->
    <div class="w-1/4 space-y-4">

      <!-- Drag & Drop Upload -->
      <div
        class="relative border border-gray-400 rounded-lg p-8 transition-colors duration-300"
        :class="videoUrl
                  ? 'bg-gray-200 cursor-not-allowed opacity-70'
                  : 'bg-white cursor-pointer hover:bg-gray-100'"
        @dragover.prevent="!videoUrl && handleDragOver($event)"
        @drop.prevent="!videoUrl && handleDrop($event)"
        @click="!videoUrl && triggerFileInput()"
      >
        <!-- Left Top Label -->
        <div class="absolute top-2 left-2 flex items-center space-x-1 text-gray-600 font-semibold">
          <span>🎥</span>
          <span>Video</span>
        </div>

        <!-- File Input -->
        <input 
          type="file" 
          ref="fileInput" 
          class="hidden" 
          @change="handleFileUpload" 
          multiple 
          accept="video/*"
        >

        <!-- 안내 글씨 (정렬 없음) -->
        <p v-if="!videoUrl">
          <span class="text-[#00008B]">Drop Video Here</span> <br>
          <span class="text-[#A0A0A0]">- or -</span> <br>
          <span class="text-[#00008B]">Click to Upload</span>
        </p>

        <!-- 업로드된 동영상 -->
        <video 
          v-if="videoUrl"
          :src="videoUrl"
          controls 
          autoplay
          class="w-full h-auto rounded-lg"
        ></video>
      </div>

      <!-- 삭제 버튼 (항상 존재) -->
      <button 
        class="mt-2 px-4 py-2 rounded text-white w-full"
        :class="videoUrl ? 'bg-red-500 hover:bg-red-600 cursor-pointer' : 'bg-gray-400 cursor-not-allowed'"
        :disabled="!videoUrl"
        @click="resetVideo"
      >
        Delete / Reset
      </button>

      <!-- 라우터 버튼 3개 (업로드 박스 아래) -->
        <div class="flex gap-4 mt-2">
          <button
            class="menu-button"
            :class="{ active: $route.path === '/prompt' }"
            @click="$router.push('/prompt')"
          >
            Prompt
          </button>
          <button
            class="menu-button"
            :class="{ active: $route.path === '/samples' }"
            @click="$router.push('/samples')"
          >
            Samples
          </button>
          <button
            class="menu-button"
            :class="{ active: $route.path === '/create-alerts' }"
            @click="$router.push('/create-alerts')"
          >
            Create Alerts
          </button>
        </div>

    </div>
  </div>
</template>

<script setup>
import { ref } from "vue"

const fileInput = ref(null)
const files = ref([])
const videoUrl = ref(null)

const triggerFileInput = () => fileInput.value.click()

const handleFileUpload = (event) => {
  const uploaded = Array.from(event.target.files)
  const videoFile = uploaded.find(f => f.type.startsWith("video/"))
  if (videoFile) {
    files.value.push(videoFile)
    videoUrl.value = URL.createObjectURL(videoFile)
  } else {
    alert("동영상 파일만 업로드할 수 있습니다.")
  }
}

const handleDrop = (e) => {
  const dropped = Array.from(e.dataTransfer.files)
  const videoFile = dropped.find(f => f.type.startsWith("video/"))
  if (videoFile) {
    files.value.push(videoFile)
    videoUrl.value = URL.createObjectURL(videoFile)
  } else {
    alert("동영상 파일만 업로드할 수 있습니다.")
  }
}

const resetVideo = () => {
  if (!videoUrl.value) return
  videoUrl.value = null
  files.value = []
  fileInput.value.value = null
}
</script>
