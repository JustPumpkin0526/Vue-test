<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <!-- Header -->
    <header class="m-2 bg-gradient-to-r from-blue-400 to-blue-600 text-white flex items-center px-6 py-3 rounded-xl shadow-md">
      <img :src="intvixLogo" alt="logo" class="w-32 h-18 mr-4" />
      <span class="font-bold text-2xl text-white drop-shadow-md">
        | VIDEO SEARCH AND SUMMARIZATION
      </span>
    </header>

    <!-- Tabs -->
    <nav class="flex border-b border-gray-200 bg-gray-100 px-4">
      <button
        v-for="tab in tabs"
        :key="tab"
        @click="activeTab = tab"
        :class="activeTab === tab
          ? 'bg-blue-100 text-blue-700 rounded-t-lg font-semibold border-b-2 border-blue-600'
          : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-t-lg'"
        class="py-2 px-5 transition"
      >
        {{ tab }}
      </button>
    </nav>

    <div class="flex flex-1 p-4 space-x-6">
      <!-- Left Panel -->
      <div class="w-1/3 space-y-6">
        <!-- Upload Box -->
        <div
          class="relative border-2 border-dashed rounded-xl p-8 transition-all duration-300 shadow-sm"
          :class="videoUrl ? 'bg-gray-200 cursor-not-allowed' : 'bg-white cursor-pointer hover:ring-2 hover:ring-blue-300'"
          @dragover.prevent
          @drop.prevent="!videoUrl && handleDrop($event)"
          @click="!videoUrl && triggerFileInput()"
        >
          <div class="absolute top-2 left-2 flex items-center space-x-1 text-gray-600 font-semibold">
            <span>🎥</span>
            <span>Video</span>
          </div>
          <input type="file" ref="fileInput" class="hidden" @change="handleFileUpload" multiple accept="video/*" />

          <p v-if="!videoUrl" class="flex flex-col items-center gap-2 text-center text-gray-600">
            <span class="text-blue-700 font-semibold">Drop Video Here</span>
            <span class="text-sm text-gray-400">or</span>
            <span class="text-blue-700 font-semibold">Click to Upload</span>
          </p>
          <video v-if="videoUrl" :src="videoUrl" controls autoplay class="w-full h-auto rounded-lg shadow-md"></video>
        </div>

        <!-- Delete/Reset -->
        <button
          class="mt-2 px-4 py-2 rounded-lg text-white w-full transition shadow-md"
          :class="videoUrl ? 'bg-red-500 hover:bg-red-600' : 'bg-gray-400 cursor-not-allowed'"
          :disabled="!videoUrl"
          @click="resetVideo"
        >
          Delete / Reset
        </button>

        <!-- Chunk Size -->
        <div class="bg-white border border-gray-300 rounded-xl p-4 shadow-sm">
          <h3 class="mb-2 font-semibold text-gray-700">CHUNK SIZE</h3>
          <div class="relative w-full" ref="dropdownRef">
            <button
              @click="toggleDropdown"
              class="w-full border border-gray-300 p-2 rounded-lg flex justify-between items-center bg-white shadow-sm hover:ring-1 hover:ring-blue-300 transition"
            >
              <span>{{ selectedLabel }}</span>
              <svg :class="{ 'rotate-180': open }" class="w-4 h-4 transition-transform duration-200"
                   xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
              </svg>
            </button>

            <transition
              enter-active-class="transition ease-out duration-100"
              enter-from-class="opacity-0 scale-y-75"
              enter-to-class="opacity-100 scale-y-100"
              leave-active-class="transition ease-in duration-100"
              leave-from-class="opacity-100 scale-y-100"
              leave-to-class="opacity-0 scale-y-75"
            >
              <ul
                v-show="open"
                class="absolute left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-10 origin-top"
              >
                <li
                  v-for="(option, index) in options"
                  :key="index"
                  class="px-4 py-2 hover:bg-blue-50 cursor-pointer transition"
                  @click.stop="selectOption(option)"
                >
                  {{ option.label }}
                </li>
              </ul>
            </transition>
          </div>
        </div>

        <!-- Prompt Accordion -->
        <div class="space-y-4">
          <div v-for="(item, index) in accordionItems" :key="index" class="border border-gray-200 rounded-xl shadow-sm overflow-hidden">
            <button
              class="w-full flex justify-between items-center px-4 py-2 font-semibold bg-gray-50 hover:bg-gray-100 transition"
              @click="toggleAccordion(index)"
            >
              {{ item.label }}
              <span>{{ item.open ? '−' : '+' }}</span>
            </button>
            <div v-show="item.open" class="p-3 bg-white">
              <textarea class="w-full border border-gray-300 rounded-lg p-2 h-20 shadow-sm focus:ring focus:ring-blue-200" v-model="item.model"></textarea>
            </div>
          </div>
        </div>

        <button class="w-full bg-blue-600 text-white py-3 rounded-lg shadow-md hover:bg-blue-700 transition" @click="submitFiles">
          Select/Upload video to summarize
        </button>
      </div>

      <!-- Right Panel -->
      <div class="w-2/3 flex flex-col space-y-6">
        <!-- Parameters button -->
        <div class="flex justify-end">
          <button class="bg-blue-600 text-white w-48 h-10 rounded-lg shadow-md hover:bg-blue-700 transition" @click="openParams">
            Show Parameters
          </button>
        </div>

        <!-- Response -->
        <div class="bg-white border border-gray-200 rounded-xl p-4 h-96 overflow-y-auto shadow-inner whitespace-pre-line">
          <div v-if="response">{{ response }}</div>
          <div v-else class="text-gray-400">Video event summary will appear here...</div>
        </div>

        <!-- Chat -->
        <div class="flex space-x-2">
          <textarea class="w-full border border-gray-300 rounded-lg p-3 h-24 shadow-sm focus:ring focus:ring-blue-200" placeholder="Ask a question" v-model="question"></textarea>
          <button class="bg-gray-300 px-5 rounded-lg shadow hover:bg-gray-400 transition" @click="askQuestion">Ask</button>
        </div>
        <div>
          <button class="bg-gray-300 px-5 py-2 rounded-lg shadow hover:bg-gray-400 transition" @click="resetChat">Reset Chat</button>
        </div>

        <!-- Parameters Popup -->
        <div v-if="isParamOpen" class="fixed inset-0 z-50" aria-modal="true" role="dialog" @click.self="closeParams">
          <!-- overlay -->
          <div class="absolute inset-0 bg-black/50"></div>

          <!-- dialog -->
          <div class="absolute right-4 top-4 bottom-4 w-[28rem] max-w-[90vw] bg-white rounded-xl shadow-2xl flex flex-col">
            <!-- header -->
            <div class="flex items-center justify-between px-4 py-3 border-b">
              <h2 class="font-semibold">Parameters</h2>
              <button class="px-2 py-1 rounded hover:bg-gray-100" @click="closeParams" aria-label="Close">✖</button>
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
                      <input type="number" min="0" max="128" v-model.number="vlm.numFrames" class="w-full border rounded px-2 py-1" />
                    </label>
                    <label class="text-sm">
                      <span class="block mb-1">VLM Input Width</span>
                      <input type="number" min="0" max="4096" v-model.number="vlm.width" class="w-full border rounded px-2 py-1" />
                    </label>
                    <label class="text-sm">
                      <span class="block mb-1">VLM Input Height</span>
                      <input type="number" min="0" max="4096" v-model.number="vlm.height" class="w-full border rounded px-2 py-1" />
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
                      <input type="number" min="1" max="1000" v-model.number="gen.topK" class="w-full border rounded px-2 py-1" />
                    </label>
                    <label class="text-sm">
                      <span class="block mb-1">Max Tokens</span>
                      <input type="number" min="1" max="1024" v-model.number="gen.maxTokens" class="w-full border rounded px-2 py-1" />
                    </label>
                    <label class="text-sm">
                      <span class="block mb-1">Seed</span>
                      <input type="number" min="1" :max="2 ** 32 - 1" v-model.number="gen.seed" class="w-full border rounded px-2 py-1" />
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
                        <input type="range" min="0" max="1" step="0.05" v-model.number="rag.summarize.topP" class="w-full" />
                        <span class="text-xs text-gray-600">{{ rag.summarize.topP }}</span>
                      </label>
                      <label class="text-sm col-span-1">
                        <span class="block mb-1">Temperature</span>
                        <input type="range" min="0" max="1" step="0.05" v-model.number="rag.summarize.temperature" class="w-full" />
                        <span class="text-xs text-gray-600">{{ rag.summarize.temperature }}</span>
                      </label>
                      <label class="text-sm col-span-1">
                        <span class="block mb-1">Max Tokens</span>
                        <input type="number" min="1" max="10240" v-model.number="rag.summarize.maxTokens" class="w-full border rounded px-2 py-1" />
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
                        <input type="range" min="0" max="1" step="0.05" v-model.number="rag.chat.temperature" class="w-full" />
                        <span class="text-xs text-gray-600">{{ rag.chat.temperature }}</span>
                      </label>
                      <label class="text-sm">
                        <span class="block mb-1">Max Tokens</span>
                        <input type="number" min="1" max="10240" v-model.number="rag.chat.maxTokens" class="w-full border rounded px-2 py-1" />
                      </label>
                    </div>
                  </details>

                  <details>
                    <summary class="cursor-pointer select-none font-medium">Alert Parameters</summary>
                    <div class="mt-2 grid grid-cols-3 gap-3">
                      <label class="text-sm">
                        <span class="block mb-1">Top P</span>
                        <input type="range" min="0" max="1" step="0.05" v-model.number="rag.notification.topP" class="w-full" />
                        <span class="text-xs text-gray-600">{{ rag.notification.topP }}</span>
                      </label>
                      <label class="text-sm">
                        <span class="block mb-1">Temperature</span>
                        <input type="range" min="0" max="1" step="0.05" v-model.number="rag.notification.temperature" class="w-full" />
                        <span class="text-xs text-gray-600">{{ rag.notification.temperature }}</span>
                      </label>
                      <label class="text-sm">
                        <span class="block mb-1">Max Tokens</span>
                        <input type="number" min="1" max="10240" v-model.number="rag.notification.maxTokens" class="w-full border rounded px-2 py-1" />
                      </label>
                    </div>
                  </details>

                  <div class="grid grid-cols-2 gap-3">
                    <label class="text-sm">
                      <span class="block mb-1">Summarize Batch Size</span>
                      <input type="number" min="1" max="1024" v-model.number="rag.summarize.batchSize" class="w-full border rounded px-2 py-1" />
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
                      <input type="number" min="1" max="1024" v-model.number="rag.batchSize" class="w-full border rounded px-2 py-1" />
                    </label>
                    <label class="text-sm">
                      <span class="block mb-1">RAG Top K</span>
                      <input type="number" min="1" max="1024" v-model.number="rag.topK" class="w-full border rounded px-2 py-1" />
                    </label>
                  </div>
                </div>
              </details>
            </div>

            <!-- footer -->
            <div class="px-4 py-3 border-t flex justify-end gap-2">
              <button class="px-3 py-1 rounded hover:bg-gray-100" @click="closeParams">Cancel</button>
              <button class="px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700" @click="applyParams">Apply</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import intvixLogo from '../logo-img/intvix_logo.png' // 파일 위치에 따라 경로 조정
import { useVssUi } from '../script/VSS_script.js'

const {
  tabs, activeTab,
  open, dropdownRef, options, selected, selectedLabel,
  toggleDropdown, selectOption,
  fileInput, files, videoUrl,
  prompts, accordionItems, toggleAccordion,
  settings, question, response,
  triggerFileInput, handleFileUpload, handleDrop, resetVideo,
  submitFiles, askQuestion, resetChat,
  isParamOpen, vlm, gen, rag,
  openParams, closeParams, applyParams,
} = useVssUi()
</script>
