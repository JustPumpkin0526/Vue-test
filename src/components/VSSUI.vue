<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="m-2 bg-blue-300 text-white flex items-center px-4 py-2">
      <img
        src="https://i.namu.wiki/i/lQVjIft7_aibqvMFpd7jJVgaccD646_WL0QrXFVbNlsdd2LDnt6YW1rCeVcdDu5BQCKxxOy24yv9mKoE8BMmCymasJfDN0royjxiG-8wr7qr6ak_AWmNyEIkXf1sEg0Qd8laY797q9uIYKzN8fznTg.webp"
        alt="logo" class="w-32 h-18 mr-2">
      <span class="font-bold text-black text-2xl">| VIDEO SEARCH AND SUMMARIZATION</span>
    </header>

    <!-- Tabs -->
    <nav class="flex border-b border-gray-300 bg-gray-100 px-4">
      <button v-for="tab in tabs" :key="tab" @click="activeTab = tab"
        :class="activeTab === tab ? 'border-b-2 border-green-600 font-semibold' : 'text-gray-600'"
        class="py-2 px-4 focus:outline-none">
        {{ tab }}
      </button>
    </nav>

    <div class="flex p-4 space-x-4">
      <!-- Left Panel -->
      <div class="w-1/3 space-y-4">
        <!-- Drag & Drop Upload
             변경: dragover는 단순 prevent만 하고, drop은 조건부로 handleDrop 호출 -->
        <div class="relative border border-gray-400 rounded-lg p-8 transition-colors duration-300"
          :class="videoUrl ? 'bg-gray-200 cursor-not-allowed' : 'bg-white cursor-pointer hover:bg-gray-100'"
          @dragover.prevent @drop.prevent="!videoUrl && handleDrop($event)" @click="!videoUrl && triggerFileInput()">
          <!-- Left Top Label -->
          <div class="absolute top-2 left-2 flex items-center space-x-1 text-gray-600 font-semibold">
            <span>🎥</span>
            <span>Video</span>
          </div>

          <!-- File Input -->
          <input type="file" ref="fileInput" class="hidden" @change="handleFileUpload" multiple accept="video/*">

          <!-- 안내 글씨 -->
          <p v-if="!videoUrl" class="flex flex-col items-center gap-1 text-center">
            <span class="text-[#00008B]">Drop Video Here</span>
            <span class="text-[#A0A0A0]">- or -</span>
            <span class="text-[#00008B]">Click to Upload</span>
          </p>

          <!-- 업로드된 동영상 -->
          <video v-if="videoUrl" :src="videoUrl" controls autoplay class="w-full h-auto rounded-lg"></video>
        </div>

        <!-- Delete / Reset 버튼 -->
        <button class="mt-2 px-4 py-2 rounded text-white w-full"
          :class="videoUrl ? 'bg-red-500 hover:bg-red-600 cursor-pointer' : 'bg-gray-400 cursor-not-allowed'"
          :disabled="!videoUrl" @click="resetVideo">
          Delete / Reset
        </button>

        <!-- CHUNK SIZE (커스텀 드롭다운) -->
        <div class="w-full h-24 bg-white border border-gray-300 rounded p-2 flex flex-col justify-start relative">
          <h3 class="mb-2">CHUNK SIZE</h3>

          <!-- 바깥 클릭 감지는 ref + document listener로 처리 (Vue에서 안전하게 사용) -->
          <div class="relative w-full" ref="dropdownRef">
            <!-- 버튼 -->
            <button @click="toggleDropdown"
              class="w-full border border-gray-300 p-2 rounded flex justify-between items-center bg-white">
              <span>{{ selectedLabel }}</span>
              <svg :class="{ 'rotate-180': open }" class="w-4 h-4 transition-transform duration-200"
                xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            <!-- 옵션 리스트 -->
            <transition enter-active-class="transition ease-out duration-100"
              enter-from-class="opacity-0 transform scale-y-75" enter-to-class="opacity-100 transform scale-y-100"
              leave-active-class="transition ease-in duration-100" leave-from-class="opacity-100 transform scale-y-100"
              leave-to-class="opacity-0 transform scale-y-75">
              <ul v-show="open"
                class="absolute left-0 right-0 mt-1 bg-white border border-gray-300 rounded shadow-md z-10 origin-top">
                <li v-for="(option, index) in options" :key="index" class="px-4 py-2 hover:bg-gray-100 cursor-pointer"
                  @click.stop="selectOption(option)">
                  {{ option.label }}
                </li>
              </ul>
            </transition>
          </div>
        </div>

        <!-- Prompt Accordion -->
        <div class="space-y-4">
          <div v-for="(item, index) in accordionItems" :key="index" class="border border-gray-300 rounded">
            <button class="w-full flex justify-between items-center p-2 font-semibold bg-white hover:bg-gray-200"
              @click="toggleAccordion(index)">
              {{ item.label }}
              <span>{{ item.open ? '−' : '+' }}</span>
            </button>

            <div v-show="item.open" class="p-2">
              <textarea class="w-full border border-gray-300 rounded p-2 h-20" v-model="item.model"></textarea>
            </div>
          </div>
        </div>

        <div class="pt-6">
          <button class="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700" @click="submitFiles">
            Select/Upload video to summarize
          </button>
        </div>

      </div>

      <!-- Right Panel -->
      <div class="w-2/3 flex flex-col space-y-4">
        <!--option area-->
        <div class="flex justify-end">
          <button class="bg-blue-600 text-white w-48 h-8 hover:bg-blue-700" @click="openParams">
            Show Parameters
          </button>
        </div>
        <!-- Response Area -->
        <div class="border border-gray-300 rounded p-4 h-96 overflow-y-auto whitespace-pre-line">
          <div v-if="response">{{ response }}</div>
          <div v-else class="text-gray-400">Video event summary will appear here...</div>
        </div>

        <!-- Chat -->
        <div class="flex space-x-2">
          <textarea class="w-full border border-gray-300 rounded p-2 h-24" placeholder="Ask a question"
            v-model="question"></textarea>
          <button class="bg-gray-300 px-4 rounded hover:bg-gray-400" @click="askQuestion">Ask</button>
        </div>
        <div class="flex space-x-2">
          <button class="bg-gray-300 px-4 rounded hover:bg-gray-400" @click="resetChat">Reset Chat</button>
        </div>
        <div v-if="isParamOpen" class="fixed inset-0 z-50" aria-modal="true" role="dialog" @click.self="closeParams">
          <!-- overlay -->
          <div class="absolute inset-0 bg-black/50"></div>

          <!-- dialog -->
          <div class="absolute right-4 top-4 bottom-4 w-[28rem] max-w-[90vw] bg-white rounded-xl shadow-2xl
                   flex flex-col">
            <!-- header -->
            <div class="flex items-center justify-between px-4 py-3 border-b">
              <h2 class="font-semibold">Parameters</h2>
              <button class="px-2 py-1 rounded hover:bg-gray-100" @click="closeParams" aria-label="Close">
                ✖
              </button>
            </div>

            <!-- content -->
            <div class="p-4 overflow-y-auto space-y-6">

              <!-- VLM Parameters -->
              <details open class="border rounded-lg">
                <summary class="cursor-pointer select-none px-3 py-2 font-medium">VLM Parameters</summary>
                <div class="p-3 space-y-3">
                  <div class="grid grid-cols-2 gap-3">
                    <label class="text-sm">
                      <span class="block mb-1">num_frames_per_chunk</span>
                      <input type="number" min="0" max="128" v-model.number="vlm.numFrames"
                        class="w-full border rounded px-2 py-1" />
                    </label>
                    <label class="text-sm">
                      <span class="block mb-1">VLM Input Width</span>
                      <input type="number" min="0" max="4096" v-model.number="vlm.width"
                        class="w-full border rounded px-2 py-1" />
                    </label>
                    <label class="text-sm">
                      <span class="block mb-1">VLM Input Height</span>
                      <input type="number" min="0" max="4096" v-model.number="vlm.height"
                        class="w-full border rounded px-2 py-1" />
                    </label>
                  </div>

                  <div class="grid grid-cols-2 gap-3">
                    <label class="text-sm">
                      <span class="block mb-1">Temperature</span>
                      <input type="range" min="0" max="1" step="0.05" v-model.number="gen.temperature" class="w-full" />
                      <span class="text-xs text-gray-600">{{ gen.temperature }}</span>
                    </label>
                    <label class="text-sm">
                      <span class="block mb-1">Top P</span>
                      <input type="range" min="0" max="1" step="0.05" v-model.number="gen.topP" class="w-full" />
                      <span class="text-xs text-gray-600">{{ gen.topP }}</span>
                    </label>
                    <label class="text-sm">
                      <span class="block mb-1">Top K</span>
                      <input type="number" min="1" max="1000" v-model.number="gen.topK"
                        class="w-full border rounded px-2 py-1" />
                    </label>
                    <label class="text-sm">
                      <span class="block mb-1">Max Tokens</span>
                      <input type="number" min="1" max="1024" v-model.number="gen.maxTokens"
                        class="w-full border rounded px-2 py-1" />
                    </label>
                    <label class="text-sm">
                      <span class="block mb-1">Seed</span>
                      <input type="number" min="1" :max="2 ** 32 - 1" v-model.number="gen.seed"
                        class="w-full border rounded px-2 py-1" />
                    </label>
                  </div>
                </div>
              </details>

              <!-- RAG Parameters -->
              <details class="border rounded-lg">
                <summary class="cursor-pointer select-none px-3 py-2 font-medium">RAG Parameters</summary>
                <div class="p-3 space-y-4">
                  <details>
                    <summary class="cursor-pointer select-none font-medium">Summarize Parameters</summary>
                    <div class="mt-2 grid grid-cols-3 gap-3">
                      <label class="text-sm col-span-1">
                        <span class="block mb-1">Top P</span>
                        <input type="range" min="0" max="1" step="0.05" v-model.number="rag.summarize.topP"
                          class="w-full" />
                        <span class="text-xs text-gray-600">{{ rag.summarize.topP }}</span>
                      </label>
                      <label class="text-sm col-span-1">
                        <span class="block mb-1">Temperature</span>
                        <input type="range" min="0" max="1" step="0.05" v-model.number="rag.summarize.temperature"
                          class="w-full" />
                        <span class="text-xs text-gray-600">{{ rag.summarize.temperature }}</span>
                      </label>
                      <label class="text-sm col-span-1">
                        <span class="block mb-1">Max Tokens</span>
                        <input type="number" min="1" max="10240" v-model.number="rag.summarize.maxTokens"
                          class="w-full border rounded px-2 py-1" />
                      </label>
                    </div>
                  </details>

                  <details>
                    <summary class="cursor-pointer select-none font-medium">Chat Parameters</summary>
                    <div class="mt-2 grid grid-cols-3 gap-3">
                      <label class="text-sm">
                        <span class="block mb-1">Top P</span>
                        <input type="range" min="0" max="1" step="0.05" v-model.number="rag.chat.topP" class="w-full" />
                        <span class="text-xs text-gray-600">{{ rag.chat.topP }}</span>
                      </label>
                      <label class="text-sm">
                        <span class="block mb-1">Temperature</span>
                        <input type="range" min="0" max="1" step="0.05" v-model.number="rag.chat.temperature"
                          class="w-full" />
                        <span class="text-xs text-gray-600">{{ rag.chat.temperature }}</span>
                      </label>
                      <label class="text-sm">
                        <span class="block mb-1">Max Tokens</span>
                        <input type="number" min="1" max="10240" v-model.number="rag.chat.maxTokens"
                          class="w-full border rounded px-2 py-1" />
                      </label>
                    </div>
                  </details>

                  <details>
                    <summary class="cursor-pointer select-none font-medium">Alert Parameters</summary>
                    <div class="mt-2 grid grid-cols-3 gap-3">
                      <label class="text-sm">
                        <span class="block mb-1">Top P</span>
                        <input type="range" min="0" max="1" step="0.05" v-model.number="rag.notification.topP"
                          class="w-full" />
                        <span class="text-xs text-gray-600">{{ rag.notification.topP }}</span>
                      </label>
                      <label class="text-sm">
                        <span class="block mb-1">Temperature</span>
                        <input type="range" min="0" max="1" step="0.05" v-model.number="rag.notification.temperature"
                          class="w-full" />
                        <span class="text-xs text-gray-600">{{ rag.notification.temperature }}</span>
                      </label>
                      <label class="text-sm">
                        <span class="block mb-1">Max Tokens</span>
                        <input type="number" min="1" max="10240" v-model.number="rag.notification.maxTokens"
                          class="w-full border rounded px-2 py-1" />
                      </label>
                    </div>
                  </details>

                  <div class="grid grid-cols-2 gap-3">
                    <label class="text-sm">
                      <span class="block mb-1">Summarize Batch Size</span>
                      <input type="number" min="1" max="1024" v-model.number="rag.summarize.batchSize"
                        class="w-full border rounded px-2 py-1" />
                    </label>
                    <label class="text-sm">
                      <span class="block mb-1">RAG Type</span>
                      <select v-model="rag.type" class="w-full border rounded px-2 py-1">
                        <option value="vector-rag">vector-rag</option>
                        <option value="graph-rag">graph-rag</option>
                      </select>
                    </label>
                    <label class="text-sm">
                      <span class="block mb-1">RAG Batch Size</span>
                      <input type="number" min="1" max="1024" v-model.number="rag.batchSize"
                        class="w-full border rounded px-2 py-1" />
                    </label>
                    <label class="text-sm">
                      <span class="block mb-1">RAG Top K</span>
                      <input type="number" min="1" max="1024" v-model.number="rag.topK"
                        class="w-full border rounded px-2 py-1" />
                    </label>
                  </div>
                </div>
              </details>
            </div>

            <!-- footer -->
            <div class="px-4 py-3 border-t flex justify-end gap-2">
              <button class="px-3 py-1 rounded hover:bg-gray-100" @click="closeParams">Cancel</button>
              <button class="px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700" @click="applyParams">
                Apply
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "MyComponent",
  mounted() {
    document.title = "Video Search and Summarization UI";
  }
};
</script>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from "vue"

const tabs = ["VIDEO FILE SUMMARIZATION & Q&A"]
const activeTab = ref(tabs[0])

// dropdown
const open = ref(false)

const dropdownRef = ref(null) // ✅ 드롭다운 DOM 참조

const options = [
  { value: 0, label: "No Chunking" },
  { value: 5, label: "5 sec" },
  { value: 10, label: "10 sec" },
  { value: 20, label: "20 sec" },
  { value: 30, label: "30 sec" },
  { value: 60, label: "1 min" },
  { value: 120, label: "2 min" },
  { value: 300, label: "5 min" },
  { value: 600, label: "10 min" },
  { value: 1200, label: "20 min" },
  { value: 1800, label: "30 min" }
]

const selected = ref(options[0].value)

const selectedLabel = computed(() => {
  const opt = options.find(o => o.value === selected.value)
  return opt ? opt.label : 'Select Chunk Size'
})

function toggleDropdown() {
  open.value = !open.value
}
function selectOption(option) {
  selected.value = option.value
  open.value = false
}

// 바깥 클릭 처리: Vue에서 안전하게 document 리스너 사용
function onDocClick(e) {
  if (!dropdownRef.value) return
  if (!dropdownRef.value.contains(e.target)) {
    open.value = false
  }
}
onMounted(() => {
  document.addEventListener('click', onDocClick)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', onDocClick)
})

// upload / accordion / other state
const fileInput = ref(null)
const files = ref([])
const videoUrl = ref(null)
const prompts = reactive({
  general: "Write a concise and clear dense caption for the provided warehouse video, focusing on irregular or hazardous events such as boxes falling, workers not wearing PPE, workers falling, workers taking photographs, workers chitchatting, forklift stuck, etc. Start and end each sentence with a time stamp.",
  caption: "You should summarize the following events of a warehouse in the format start_time:end_time:caption. For start_time and end_time use . to seperate seconds, minutes, hours. If during a time segment only regular activities happen, then ignore them, else note any irregular activities in detail. The output should be bullet points in the format start_time:end_time: detailed_event_description. Don't return anything else except the bullet points.",
  aggregation: "You are a warehouse monitoring system. Given the caption in the form start_time:end_time: caption, Aggregate the following captions in the format start_time:end_time:event_description. If the event_description is the same as another event_description, aggregate the captions in the format start_time1:end_time1,...,start_timek:end_timek:event_description. If any two adjacent end_time1 and start_time2 is within a few tenths of a second, merge the captions in the format start_time1:end_time2. The output should only contain bullet points.  Cluster the output into Unsafe Behavior, Operational Inefficiencies, Potential Equipment Damage and Unauthorized Personnel"
})
const accordionItems = reactive([
  { label: 'Prompt', model: prompts.general, open: false },
  { label: 'Caption Summarization Prompt', model: prompts.caption, open: false },
  { label: 'Summary Aggregation Prompt', model: prompts.aggregation, open: false }
])
const toggleAccordion = (index) => {
  accordionItems[index].open = !accordionItems[index].open
}
const settings = ref({
  enableChat: true,
  enableHistory: true,
})
const question = ref("")
const response = ref("")

const triggerFileInput = () => fileInput.value?.click()

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
  if (fileInput.value) fileInput.value.value = null
}

// Submit VSS
const VSS_API_URL = "http://localhost:7100/gradio_api/queue/join"; // Python 백엔드 주소로 변경
const submitFiles = async () => {
  if (!files.value.length) {
    alert("Please upload a video file first.")
    return
  }

  // 각 프롬프트 값을 분리해서 추출
  const prompt = accordionItems[0].model
  const csprompt = accordionItems[1].model
  const saprompt = accordionItems[2].model

  console.log(selected.value);

  const formData = new FormData();
  formData.append("file", files.value[0]);
  formData.append("prompt", prompt);
  formData.append("csprompt", csprompt);
  formData.append("saprompt", saprompt);
  formData.append("chunk_duration", selected.value);

  response.value = "⏳ Sending video + prompt to backend for summarization...";

  try {
    const res = await fetch(VSS_API_URL, {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    response.value = `✅ Summarization Completed!\n\n${data.summary || JSON.stringify(data, null, 2)}`;
  } catch (err) {
    response.value = "❌ Failed to send video. Please check server.";
  }
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

// === Parameters Popup State ===
const isParamOpen = ref(false)

// 예시 파라미터 상태 (Gradio의 UI 구조를 반영한 기본값들)
const vlm = reactive({
  numFrames: 0,
  width: 0,
  height: 0,
})

const gen = reactive({
  temperature: 0.4,
  topP: 1,
  topK: 100,
  maxTokens: 512,
  seed: 1,
})

const rag = reactive({
  type: 'graph-rag',
  batchSize: 1,
  topK: 5,
  summarize: {
    topP: 0.7,
    temperature: 0.2,
    maxTokens: 2048,
    batchSize: 6,
  },
  chat: {
    topP: 0.7,
    temperature: 0.2,
    maxTokens: 512,
  },
  notification: {
    topP: 0.7,
    temperature: 0.2,
    maxTokens: 2048,
  },
})

function openParams() {
  isParamOpen.value = true
  // (선택) 스크롤 잠그기
  document.documentElement.style.overflow = 'hidden'
}

function closeParams() {
  isParamOpen.value = false
  document.documentElement.style.overflow = ''
}

// 실제 적용 시 백엔드로 반영하거나, 기존 submit 로직에 주입
function applyParams() {
  // 예: formData에 같이 넣거나, 전역 설정으로 사용
  // console.log({ vlm, gen, rag })
  closeParams()
}

// ESC로 닫기
function onKeydown(e) {
  if (e.key === 'Escape' && isParamOpen.value) closeParams()
}

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
})
onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
})
</script>
