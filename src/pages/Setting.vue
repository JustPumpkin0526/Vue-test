<template>
  <div class="border-2 px-3 py-3 bg-gray-100 mb-3">
    <button class="w-full text-left flex items-center gap-2" @click="toggleVlmParams">
      <h2>VLM Parameters</h2>
      <span class="ml-auto">{{ showVlmParams ? '▲' : '▼' }}</span>
    </button>
    <div :class="[showVlmParams ? 'block' : 'hidden', 'mt-3']">
      <div class="grid lg:grid-cols-3 gap-4 rounded-md">
        <section class="rounded-2xl border-2 px-2 py-3 min-w-[220px] bg-white">
          <h2 class="font-semibold mb-3">Chunk 설정</h2>
          <label class="block text-sm mb-1">Chunk Size</label>
          <p class="text-xs text-gray-500 mt-2">동영상 추론에서 분할 단위를 설정합니다.</p>
          <select v-model.number="chunk" class="border-2 border-gray-300 rounded-md px-3 py-2 w-full mt-3">
            <option value=0>No chunking</option>
            <option value=5>5 sec</option>
            <option value=10>10 sec</option>
            <option value=20>20 sec</option>
            <option value=30>30 sec</option>
            <option value=60>1 min</option>
            <option value=120>2 min</option>
            <option value=300>5 min</option>
            <option value=600>10 min</option>
            <option value=1200>20 min</option>
            <option value=1800>30 min</option>
          </select>
        </section>

        <section class="rounded-2xl border-2 px-2 py-3 min-w-[220px] bg-white">
          <h2 class="font-semibold mb-3">Caption Summarization Prompt</h2>
          <textarea v-model="captionPrompt" rows="6" class="w-full border-2 border-gray-300 rounded-md p-3"></textarea>
        </section>

        <section class="rounded-2xl border-2 px-2 py-3 min-w-[220px] bg-white">
          <h2 class="font-semibold mb-3">Summary Aggregation Prompt</h2>
          <textarea v-model="aggregationPrompt" rows="6"
            class="w-full border-2 border-gray-300 rounded-md p-3"></textarea>
        </section>
      </div>

      <div class="grid lg:grid-cols-3 gap-4 mt-4 rounded-md">
        <section class="rounded-2xl border-2 px-2 py-3 min-w-[220px] bg-white">
          <h2 class="font-semibold mb-3">num_frames_per_chunk</h2>
          <p class="text-xs text-gray-500 mt-2">The number of frames to choose from chunk</p>
          <input v-model.number="nfmc" type="number" min="0" max="256" step="1"
            class="border-2 border-gray-300 rounded-md px-3 py-2 w-full mt-3" />
        </section>

        <section class="rounded-2xl border-2 px-2 py-3 min-w-[220px] bg-white">
          <h2 class="font-semibold mb-3">VLM Input Width</h2>
          <p class="text-xs text-gray-500 mt-2">Provide VLM frame's width details</p>
          <input v-model.number="frameWidth" type="number" min="0" max="4096" step="1"
            class="border-2 border-gray-300 rounded-md px-3 py-2 w-full mt-3" />
        </section>

        <section class="rounded-2xl border-2 px-2 py-3 min-w-[220px] bg-white">
          <h2 class="font-semibold mb-3">VLM Input Height</h2>
          <p class="text-xs text-gray-500 mt-2">Provide VLM frame's height details</p>
          <input v-model.number="frameHeight" type="number" min="0" max="4096" step="1"
            class="border-2 border-gray-300 rounded-md px-3 py-2 w-full mt-3" />
        </section>
      </div>

      <div class="grid lg:grid-cols-3 gap-4 mt-4 rounded-md">
        <section class="rounded-2xl border-2 px-2 py-3 min-w-[220px] bg-white">
          <h2 class="font-semibold mb-3">Top-k</h2>
          <p class="text-xs text-gray-500 mt-2">The number of highest probability vocabulary tokens to keep for
            top-k-filtering</p>
          <input v-model.number="topk" type="number" min="1" max="1000" step="1"
            class="border-2 border-gray-300 rounded-md px-3 py-2 w-full mt-3" />
        </section>

        <section class="rounded-2xl border-2 px-2 py-3 min-w-[220px] bg-white">
          <h2 class="font-semibold mb-3">Top-p</h2>
          <p class="text-xs text-gray-500 mt-2">The top-p sampling mass used for text generation. The top-p value
            determines the probability mass that is sampled at sampling time. For example, if top_p = 0.2, only the most
            likely tokens (summing to 0.2 cumulative probability) will be sampled. It is not recommended to modify both
            temperature and top_p in the same call.</p>
          <div>
            <input v-model.number="topp" type="number" min="0" max="1" step="0.1" class="border-2 border-gray-300 w-20 mt-3 text-center" />
            <button class="border-2 border-gray-300 w-7" @click="reset_TopP">↺</button>
          </div>
          
          <div class="flex items-end h-10">
            <input v-model.number="topp" type="range" min="0" max="1" step="0.05"
              class="w-11/12 mx-auto border-gray-300" />
          </div>
        </section>

        <section class="rounded-2xl border-2 px-2 py-3 min-w-[220px] bg-white">
          <h2 class="font-semibold mb-3">Temperature</h2>
          <p class="text-xs text-gray-500 mt-2">The sampling temperature to use for text generation. The higher the
            temperature value is, the less deterministic the output text will be. It is not recommended to modify both
            temperature and top_p in the same call.</p>
          <div>
            <input v-model.number="temp" type="number" min="0" max="1" step="0.1" class="border-2 border-gray-300 w-20 mt-3 text-center" />
            <button class="border-2 border-gray-300 w-7" @click="reset_Temperature">↺</button>
          </div>
          
          <div class="flex items-end h-10">
            <input v-model.number="temp" type="range" min="0" max="1" step="0.05"
              class="w-11/12 mx-auto border-gray-300" />
          </div>
        </section>
      </div>

      <div class="grid lg:grid-cols-2 gap-4 mt-4 rounded-md">
        <section class="rounded-2xl border-2 px-2 py-3 min-w-[220px] bg-white">
          <div class="flex items-center gap-2">
            <div><h2 class="font-semibold">Max Tokens</h2>
            <p class="text-xs text-gray-500">The maximum number of tokens to generate in any given call. Note that
            the
            model is not aware of this value, and generation will simply stop at the number of tokens specified.</p>
            </div>

            <div class="ml-auto">
              <input v-model.number="maxTokens" type="number" min="1" max="1024" step="1" class="border-2 border-gray-300 w-20 text-center" />
              <button class="border-2 border-gray-300 w-7" @click="reset_MaxTokens">↺</button>
            </div>
          </div>
        
          <div class="flex items-end h-10">
            <span class="text-xs text-gray-400 w-8 text-center">1</span>
            <input v-model.number="maxTokens" type="range" min="1" max="1024" step="1"
              class="w-11/12 mx-auto border-gray-300" />
            <span class="text-xs text-gray-400 w-12 text-center">1024</span>
          </div>
        </section>

        <section class="rounded-2xl border-2 px-2 py-3 min-w-[220px] bg-white">
          <h2 class="font-semibold mb-3">seed</h2>
          <p class="text-xs text-gray-500 mt-2">Seed value to use for sampling. Repeated requests with the same seed and
            parameters should return the same result.</p>
          <input v-model.number="seed" type="number" min="1" max="4294967295" step="1" class="border-2 border-gray-300 rounded-md px-3 py-2 w-full mt-3" />
        </section>
      </div>
    </div>
  </div>

  <div class="border-2 px-3 py-3 bg-gray-100">
    <button class="w-full text-left flex items-center gap-2" @click="toggleRAGParams">
      <h2>RAG Parameters</h2>
      <span class="ml-auto">{{ showRAGParams ? '▲' : '▼' }}</span>
    </button>

    <!--Summarize Parameters-->
    <div :class="[showRAGParams ? 'block' : 'hidden', 'mt-3', 'border-2', 'border-gray-300']">
      <button class="w-full text-left rounded-md px-3 py-2 flex items-center gap-2"  @click="toggleSUMMARYParams">
        <span>Summarize Parameters</span>
        <span class="ml-auto">{{ showSUMMARYParams ? '▲' : '▼' }}</span>
      </button>
      <div :class="[showSUMMARYParams ? 'block' : 'hidden', 'mt-3', 'm-3']">
        <section class="rounded-2xl border-2 px-2 py-3 min-w-[220px] bg-white">
          <div class="flex items-center gap-2">
            <label>
              <h2 class="font-semibold">Summarize Top P</h2>
              <p class="text-xs text-gray-500">The top-p sampling mass used for summarization. Determines the probability mass that is sampled.</p>
            </label>
            <div class="ml-auto">
              <input v-model.number="S_TopP" type="number" min="0" max="1" step="0.05"
                class="border-2 border-gray-300 w-28 text-center" />
              <button class="border-2 border-gray-300 w-7" @click="resetS_TopP">↺</button>
            </div>
          </div>
          <div class="flex items-end h-10">
            <span class="text-xs text-gray-400 w-10 text-center">0</span>
            <input v-model.number="S_TopP" type="range" min="0" max="1" step="0.05"
              class="w-full border-gray-300" />
            <span class="text-xs text-gray-400 w-10 text-center">1</span>
          </div>
        </section>

        <section class="rounded-2xl border-2 px-2 py-3 min-w-[220px] bg-white">
          <div class="flex items-center gap-2">
            <label>
              <h2 class="font-semibold">Summarize Temperature</h2>
              <p class="text-xs text-gray-500">The sampling temperature to use for summarization. Higher values make the output less deterministic.</p>
            </label>
            <div class="ml-auto">
              <input v-model.number="S_TEMPERATURE" type="number" min="0" max="1" step="0.05"
                class="border-2 border-gray-300 w-28 text-center" />
              <button class="border-2 border-gray-300 w-7" @click="resetS_TEMPERATURE">↺</button>
            </div>
          </div>
          <div class="flex items-end h-10">
            <span class="text-xs text-gray-400 w-10 text-center">0</span>
            <input v-model.number="S_TEMPERATURE" type="range" min="0" max="1" step="0.05"
              class="w-full border-gray-300" />
            <span class="text-xs text-gray-400 w-10 text-center">1</span>
          </div>
        </section>

        <section class="rounded-2xl border-2 px-2 py-3 min-w-[220px] bg-white">
          <div class="flex items-center gap-2">
            <label>
              <h2 class="font-semibold">Summarize Max Tokens</h2>
              <p class="text-xs text-gray-500">The maximum number of tokens to generate for summarization.</p>
            </label>
            <div class="ml-auto">
              <input v-model.number="SMAX_TOKENS" type="number" min="1" max="10240" step="1"
              class="border-2 border-gray-300 w-28 text-center" />
              <button class="border-2 border-gray-300 w-7" @click="resetSMAX_TOKENS">↺</button>
            </div>
          </div>
          <div class="flex items-end h-10">
            <span class="text-xs text-gray-400 w-10 text-center">0</span>
            <input v-model.number="SMAX_TOKENS" type="range" min="1" max="10240" step="1"
              class="w-full border-gray-300" />
            <span class="text-xs text-gray-400 w-10 text-center">10240</span>
          </div>
        </section>
      </div>
    </div>

    <!-- Chat parameters-->
    <div :class="[showRAGParams ? 'block' : 'hidden', 'mt-3', 'border-2', 'border-gray-300']">
      <button class="w-full text-left rounded-md px-3 py-2 flex items-center gap-2"  @click="toggleChatParams">
        <span>Chat Parameters</span>
        <span class="ml-auto">{{ showChatParams ? '▲' : '▼' }}</span>
      </button>
      <div :class="[showChatParams ? 'block' : 'hidden', 'mt-3', 'm-3']">
        <section class="rounded-2xl border-2 px-2 py-3 min-w-[220px] bg-white">
          <div class="flex items-center gap-2">
            <label>
              <h2 class="font-semibold">Chat Top P</h2>
              <p class="text-xs text-gray-500">The top-p sampling mass used for chat. Determines the probability mass that is sampled.</p>
            </label>
            <div class="ml-auto">
              <input v-model.number="C_TopP" type="number" min="0" max="1" step="0.05"
                class="border-2 border-gray-300 w-28 text-center" />
              <button class="border-2 border-gray-300 w-7" @click="resetC_TopP">↺</button>
            </div>
          </div>
          <div class="flex items-end h-10">
            <span class="text-xs text-gray-400 w-10 text-center">0</span>
            <input v-model.number="C_TopP" type="range" min="0" max="1" step="0.05"
              class="w-full border-gray-300" />
            <span class="text-xs text-gray-400 w-10 text-center">1</span>
          </div>
        </section>

        <section class="rounded-2xl border-2 px-2 py-3 min-w-[220px] bg-white">
          <div class="flex items-center gap-2">
            <label>
              <h2 class="font-semibold">Chat Temperature</h2>
              <p class="text-xs text-gray-500">The sampling temperature to use for chat. Higher values make the output less deterministic.</p>
            </label>
            <div class="ml-auto">
              <input v-model.number="C_TEMPERATURE" type="number" min="0" max="1" step="0.05"
                class="border-2 border-gray-300 w-28 text-center" />
              <button class="border-2 border-gray-300 w-7" @click="resetC_TEMPERATURE">↺</button>
            </div>
          </div>
          <div class="flex items-end h-10">
            <span class="text-xs text-gray-400 w-10 text-center">0</span>
            <input v-model.number="C_TEMPERATURE" type="range" min="0" max="1" step="0.05"
              class="w-full border-gray-300" />
            <span class="text-xs text-gray-400 w-10 text-center">1</span>
          </div>
        </section>

        <section class="rounded-2xl border-2 px-2 py-3 min-w-[220px] bg-white">
          <div class="flex items-center gap-2">
            <label>
              <h2 class="font-semibold">Chat Max Tokens</h2>
              <p class="text-xs text-gray-500">The maximum number of tokens to generate for chat.</p>
            </label>
            <div class="ml-auto">
              <input v-model.number="C_MAX_TOKENS" type="number" min="1" max="10240" step="1"
              class="border-2 border-gray-300 w-28 text-center" />
              <button class="border-2 border-gray-300 w-7" @click="resetC_MAX_TOKENS">↺</button>
            </div>
          </div>
          <div class="flex items-end h-10">
            <span class="text-xs text-gray-400 w-10 text-center">0</span>
            <input v-model.number="C_MAX_TOKENS" type="range" min="1" max="10240" step="1"
              class="w-full border-gray-300" />
            <span class="text-xs text-gray-400 w-10 text-center">10240</span>
          </div>
        </section>
      </div>
    </div>

    <!-- Alert Parameters -->
    <div :class="[showRAGParams ? 'block' : 'hidden', 'mt-3', 'border-2', 'border-gray-300']">
      <button class="w-full text-left rounded-md px-3 py-2 flex items-center gap-2"  @click="toggleAlertParams">
        <span>Alert Parameters</span>
        <span class="ml-auto">{{ showAlertParams ? '▲' : '▼' }}</span>
      </button>
      <div :class="[showAlertParams ? 'block' : 'hidden', 'mt-3', 'm-3']">
        <section class="rounded-2xl border-2 px-2 py-3 min-w-[220px] bg-white">
          <div class="flex items-center gap-2">
            <label>
              <h2 class="font-semibold">Alert Top P</h2>
              <p class="text-xs text-gray-500">The top-p sampling mass used for alerts. Determines the probability mass that is sampled.</p>
            </label>
            <div class="ml-auto">
              <input v-model.number="A_TopP" type="number" min="0" max="1" step="0.05"
                class="border-2 border-gray-300 w-28 text-center" />
              <button class="border-2 border-gray-300 w-7" @click="resetA_TopP">↺</button>
            </div>
          </div>
          <div class="flex items-end h-10">
            <span class="text-xs text-gray-400 w-10 text-center">0</span>
            <input v-model.number="A_TopP" type="range" min="0" max="1" step="0.05"
              class="w-full border-gray-300" />
            <span class="text-xs text-gray-400 w-10 text-center">1</span>
          </div>
        </section>

        <section class="rounded-2xl border-2 px-2 py-3 min-w-[220px] bg-white">
          <div class="flex items-center gap-2">
            <label>
              <h2 class="font-semibold">Alert Temperature</h2>
              <p class="text-xs text-gray-500">The sampling temperature to use for alerts. Higher values make the output less deterministic.</p>
            </label>
            <div class="ml-auto">
              <input v-model.number="A_TEMPERATURE" type="number" min="0" max="1" step="0.05"
                class="border-2 border-gray-300 w-28 text-center" />
              <button class="border-2 border-gray-300 w-7" @click="resetA_TEMPERATURE">↺</button>
            </div>
          </div>
          <div class="flex items-end h-10">
            <span class="text-xs text-gray-400 w-10 text-center">0</span>
            <input v-model.number="A_TEMPERATURE" type="range" min="0" max="1" step="0.05"
              class="w-full border-gray-300" />
            <span class="text-xs text-gray-400 w-10 text-center">1</span>
          </div>
        </section>

        <section class="rounded-2xl border-2 px-2 py-3 min-w-[220px] bg-white">
          <div class="flex items-center gap-2">
            <label>
              <h2 class="font-semibold">Alert Max Tokens</h2>
              <p class="text-xs text-gray-500">The maximum number of tokens to generate for alerts.</p>
            </label>
            <div class="ml-auto">
              <input v-model.number="A_MAX_TOKENS" type="number" min="1" max="10240" step="1"
              class="border-2 border-gray-300 w-28 text-center" />
              <button class="border-2 border-gray-300 w-7" @click="resetA_MAX_TOKENS">↺</button>
            </div>
          </div>
          <div class="flex items-end h-10">
            <span class="text-xs text-gray-400 w-10 text-center">0</span>
            <input v-model.number="A_MAX_TOKENS" type="range" min="1" max="10240" step="1"
              class="w-full border-gray-300" />
            <span class="text-xs text-gray-400 w-10 text-center">10240</span>
          </div>
        </section>
      </div>
    </div>

    <!--Batch Size-->
    <div class="grid lg:grid-cols-1 gap-4 rounded-md, mt-3">
      <section class="rounded-2xl border-2 px-2 py-3 min-w-[220px] bg-white">
        <h2 class="font-semibold mb-3">Summarize Batch Size</h2>
          <p class="text-xs text-gray-500 mt-2">Batch size for summarization.</p>
          <input v-model.number="batch" type="number" min="1" max="1024" step="1"
            class="border-2 border-gray-300 rounded-md px-3 py-2 w-full mt-3" />
      </section>
    </div>

    <!-- RAG settings -->
    <div class="grid lg:grid-cols-2 gap-4 rounded-md, mt-3">
      <section class="rounded-2xl border-2 px-2 py-3 min-w-[220px] bg-white">
        <h2 class="font-semibold mb-3">RAG Batch Size</h2>
          <p class="text-xs text-gray-500 mt-2">Batch size for RAG processing.</p>
          <input v-model.number="RAG_batch" type="number" min="1" max="1024" step="1"
            class="border-2 border-gray-300 rounded-md px-3 py-2 w-full mt-3" />
      </section>
      <section class="rounded-2xl border-2 px-2 py-3 min-w-[220px] bg-white">
        <h2 class="font-semibold mb-3">RAG Top K</h2>
          <p class="text-xs text-gray-500 mt-2">The number of highest probability vocabulary tokens to keep for RAG top-k-filtering.</p>
          <input v-model.number="RAG_topk" type="number" min="1" max="1024" step="1"
            class="border-2 border-gray-300 rounded-md px-3 py-2 w-full mt-3" />
      </section>
    </div>

  </div>
</template>

<script setup>
import { ref, provide } from "vue";

//VLM parameters
const showVlmParams = ref(true);
function toggleVlmParams() {
  showVlmParams.value = !showVlmParams.value;
}

const chunk = ref(0);
const captionPrompt = ref("You will be given captions from sequential clips of a video. Aggregate captions in the format start_time:end_time:caption based on whether captions are related to one another or create a continuous scene.");
const aggregationPrompt = ref("Based on the available information, generate a summary that captures the important events in the video. The summary should be organized chronologically and in logical sections. This should be a concise, yet descriptive summary of all the important events. The format should be intuitive and easy for a user to read and understand what happened. Format the output in Markdown so it can be displayed nicely. Timestamps are in seconds so please format them as SS.SSS");
const nfmc = ref(0);
const frameWidth = ref(0);
const frameHeight = ref(0);
const topk = ref(100);
const topp = ref(1.0);
const temp = ref(0.4);
const maxTokens = ref(512);
const seed = ref(1);

const reset_TopP = () => {
  topp.value = 1.0;
};
const reset_Temperature = () => {
  temp.value = 0.4;
};
const reset_MaxTokens = () => {
  maxTokens.value = 512;
};

//RAG parameters
const batch = ref(6);
const RAG_batch = ref(1);
const RAG_topk = ref(5);

const showRAGParams = ref(true);
function toggleRAGParams() {
  showRAGParams.value = !showRAGParams.value;
}
//Summary parameters
const showSUMMARYParams = ref(false);
function toggleSUMMARYParams() {
  showSUMMARYParams.value = !showSUMMARYParams.value;
}

const S_TopP = ref(0.7);
const S_TEMPERATURE = ref(0.2);
const SMAX_TOKENS = ref(2048);

const resetS_TopP = () => {
  S_TopP.value = 0.7;
};
const resetS_TEMPERATURE = () => {
  S_TEMPERATURE.value = 0.2;
};
const resetSMAX_TOKENS = () => {
  SMAX_TOKENS.value = 2048;
};

//Chat parameters
const showChatParams = ref(false);
function toggleChatParams() {
  showChatParams.value = !showChatParams.value;
}

const C_TopP = ref(0.7);
const C_TEMPERATURE = ref(0.2);
const C_MAX_TOKENS = ref(2048);

const resetC_TopP = () => {
  C_TopP.value = 0.7;
};
const resetC_TEMPERATURE = () => {
  C_TEMPERATURE.value = 0.2;
};
const resetC_MAX_TOKENS = () => {
  C_MAX_TOKENS.value = 2048;
};

//Alert parameters
const showAlertParams = ref(false);
function toggleAlertParams() {
  showAlertParams.value = !showAlertParams.value;
}

const A_TopP = ref(0.7);
const A_TEMPERATURE = ref(0.2);
const A_MAX_TOKENS = ref(2048);

const resetA_TopP = () => {
  A_TopP.value = 0.7;
};
const resetA_TEMPERATURE = () => {
  A_TEMPERATURE.value = 0.2;
};
const resetA_MAX_TOKENS = () => {
  A_MAX_TOKENS.value = 2048;
};

provide("summaryParams", {
  chunk,
  captionPrompt,
  aggregationPrompt,
  nfmc,
  frameWidth,
  frameHeight,
  topk,
  topp,
  temp,
  maxTokens,
  seed,
  batch,
  RAG_batch,
  RAG_topk,
  S_TopP,
  S_TEMPERATURE,
  SMAX_TOKENS,
  C_TopP,
  C_TEMPERATURE,
  C_MAX_TOKENS,
  A_TopP,
  A_TEMPERATURE,
  A_MAX_TOKENS
});
</script>
