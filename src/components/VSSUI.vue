<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-black text-white flex items-center px-4 py-2">
      <img src="https://upload.wikimedia.org/wikipedia/commons/4/44/NVIDIA_logo.svg" alt="NVIDIA" class="h-6 mr-2">
      <span class="font-bold">VIDEO SEARCH AND SUMMARIZATION AGENT</span>
    </header>

    <!-- Tabs -->
    <nav class="flex border-b border-gray-300 bg-gray-100 px-4">
      <button
        v-for="tab in tabs"
        :key="tab"
        @click="activeTab = tab"
        :class="activeTab === tab ? 'border-b-2 border-green-600 font-semibold' : 'text-gray-600'"
        class="py-2 px-4 focus:outline-none"
      >
        {{ tab }}
      </button>
    </nav>

    <div class="flex p-4 space-x-4">
      <!-- Left Panel -->
      <div class="w-1/3 space-y-4">
        <!-- Drag & Drop Upload -->
        <div
          class="border-2 border-dashed border-gray-400 rounded-lg p-8 text-center cursor-pointer hover:bg-gray-100"
          @dragover.prevent
          @drop.prevent="handleDrop"
          @click="triggerFileInput"
        >
          <input type="file" ref="fileInput" class="hidden" @change="handleFileUpload" multiple>
          <p>Drop Video Here <br> - or - <br> Click to Upload</p>
        </div>

        <!-- File List Preview -->
        <div v-if="files.length" class="space-y-2">
          <p class="font-semibold">Uploaded Files:</p>
          <ul class="list-disc list-inside text-sm">
            <li v-for="f in files" :key="f.name">{{ f.name }}</li>
          </ul>
        </div>

        <!-- Prompt Inputs -->
        <div class="space-y-2">
          <label class="font-semibold">Prompt</label>
          <textarea class="w-full border border-gray-300 rounded p-2 h-20" v-model="prompts.general"></textarea>
        </div>
        <div class="space-y-2">
          <label class="font-semibold">Caption Summarization Prompt</label>
          <textarea class="w-full border border-gray-300 rounded p-2 h-20" v-model="prompts.caption"></textarea>
        </div>
        <div class="space-y-2">
          <label class="font-semibold">Summary Aggregation Prompt</label>
          <textarea class="w-full border border-gray-300 rounded p-2 h-20" v-model="prompts.aggregation"></textarea>
        </div>

        <!-- Settings -->
        <div class="space-y-1">
          <label class="font-semibold">File Settings</label>
          <div>
            <label class="flex items-center space-x-2">
              <input type="checkbox" v-model="settings.enableChat">
              <span>Enable Chat for the file</span>
            </label>
          </div>
          <div>
            <label class="flex items-center space-x-2">
              <input type="checkbox" v-model="settings.enableHistory">
              <span>Enable chat history</span>
            </label>
          </div>
        </div>

        <button class="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700" @click="submitFiles">
          Select/Upload video to summarize
        </button>
      </div>

      <!-- Right Panel -->
      <div class="w-2/3 flex flex-col space-y-4">
        <!-- Chat -->
        <div class="flex space-x-2">
          <textarea
            class="w-full border border-gray-300 rounded p-2 h-24"
            placeholder="Ask a question"
            v-model="question"
          ></textarea>
          <button class="bg-gray-300 px-4 rounded hover:bg-gray-400" @click="askQuestion">Ask</button>
        </div>
        <div class="flex space-x-2">
          <button class="bg-gray-300 px-4 rounded hover:bg-gray-400" @click="generateScenario">Generate Scenario Highlight</button>
          <button class="bg-gray-300 px-4 rounded hover:bg-gray-400" @click="generateHighlight">Generate Highlight</button>
          <button class="bg-gray-300 px-4 rounded hover:bg-gray-400" @click="resetChat">Reset Chat</button>
        </div>

        <!-- Response Area -->
        <div class="border border-gray-300 rounded p-4 h-96 overflow-y-auto whitespace-pre-line">
          <div v-if="response">{{ response }}</div>
          <div v-else class="text-gray-400">Video event summary will appear here...</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue"

const tabs = ["VIDEO FILE SUMMARIZATION & Q&A", "LIVE STREAM SUMMARIZATION", "IMAGE FILE SUMMARIZATION & Q&A"]
const activeTab = ref(tabs[0])

const fileInput = ref(null)
const files = ref([])
const prompts = ref({
  general: "",
  caption: "",
  aggregation: "",
})
const settings = ref({
  enableChat: true,
  enableHistory: true,
})
const question = ref("")
const response = ref("")

// Drag & Drop
const handleDrop = (e) => {
  const dropped = Array.from(e.dataTransfer.files)
  files.value.push(...dropped)
}

// File Input
const triggerFileInput = () => fileInput.value.click()
const handleFileUpload = (event) => {
  const uploaded = Array.from(event.target.files)
  files.value.push(...uploaded)
}

// Submit
const submitFiles = async () => {
  if (!files.value.length) {
    alert("Please upload a video file first.")
    return
  }
  // 예: Summarization API 호출 (가짜 fetch)
  response.value = "⏳ Summarizing video..."
  setTimeout(() => {
    response.value = "✅ Video summary completed.\n- Event A\n- Event B\n- Event C"
  }, 2000)
}

// Chat
const askQuestion = async () => {
  if (!question.value) return
  response.value += `\n\nQ: ${question.value}\nA: Placeholder answer from API.`
  question.value = ""
}

const generateScenario = () => response.value += "\n\n📌 Scenario Highlight generated."
const generateHighlight = () => response.value += "\n\n✨ Highlight generated."
const resetChat = () => response.value = ""
</script>
