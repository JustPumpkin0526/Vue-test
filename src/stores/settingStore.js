// src/stores/settingStore.js
import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useSettingStore = defineStore('setting', () => {
  const captionPrompt = ref("You will be given captions from sequential clips of a video. Aggregate captions in the format start_time:end_time:caption based on whether captions are related to one another or create a continuous scene.");
  const aggregationPrompt = ref("Based on the available information, generate a summary that captures the important events in the video. The summary should be organized chronologically and in logical sections. This should be a concise, yet descriptive summary of all the important events. The format should be intuitive and easy for a user to read and understand what happened. Format the output in Markdown so it can be displayed nicely. Timestamps are in seconds so please format them as SS.SSS");
  const chunk = ref(0);
  const nfmc = ref(0);
  const frameWidth = ref(0);
  const frameHeight = ref(0);
  const topk = ref(100);
  const topp = ref(1.0);
  const temp = ref(0.4);
  const maxTokens = ref(512);
  const seed = ref(1);
  const batch = ref(6);
  const RAG_batch = ref(1);
  const RAG_topk = ref(5);
  const S_TopP = ref(0.7);
  const S_TEMPERATURE = ref(0.2);
  const SMAX_TOKENS = ref(2048);
  const C_TopP = ref(0.7);
  const C_TEMPERATURE = ref(0.2);
  const C_MAX_TOKENS = ref(2048);
  const A_TopP = ref(0.7);
  const A_TEMPERATURE = ref(0.2);
  const A_MAX_TOKENS = ref(2048);
  const enableAudio = ref(false);

  return {
    captionPrompt, aggregationPrompt, chunk, nfmc, frameWidth, frameHeight,
    topk, topp, temp, maxTokens, seed, batch, RAG_batch, RAG_topk,
    S_TopP, S_TEMPERATURE, SMAX_TOKENS, C_TopP, C_TEMPERATURE, C_MAX_TOKENS,
    A_TopP, A_TEMPERATURE, A_MAX_TOKENS, enableAudio
  };
});