// src/stores/settingStore.js
import { defineStore } from 'pinia';
import { ref, watch } from 'vue';

// localStorage에서 테마 불러오기
const getStoredTheme = () => {
  const stored = localStorage.getItem('vss_theme');
  if (stored) return stored;
  
  // 시스템 설정 확인
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'auto';
  }
  return 'light';
};

// localStorage에서 언어 불러오기
const getStoredLanguage = () => {
  const stored = localStorage.getItem('vss_language');
  return stored || 'ko'; // 기본값은 한국어
};

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
  
  // 테마 상태 (light, dark, auto)
  const theme = ref(getStoredTheme());
  
  // 언어 상태 (ko, en)
  const language = ref(getStoredLanguage());

  // 테마 적용 함수 (watch보다 먼저 정의)
  const applyTheme = (themeValue) => {
    const root = document.documentElement;
    let isDark = false;

    if (themeValue === 'dark') {
      isDark = true;
    } else if (themeValue === 'auto') {
      // 시스템 설정 확인
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        isDark = true;
      }
    }

    if (isDark) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  };

  // 테마 변경 감지 및 localStorage 저장
  watch(theme, (newTheme) => {
    localStorage.setItem('vss_theme', newTheme);
    applyTheme(newTheme);
  }, { immediate: true });

  // 언어 변경 감지 및 localStorage 저장
  watch(language, (newLanguage) => {
    localStorage.setItem('vss_language', newLanguage);
  }, { immediate: true });

  // 시스템 테마 변경 감지 (auto 모드일 때)
  if (window.matchMedia) {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaQuery.addEventListener('change', () => {
      if (theme.value === 'auto') {
        applyTheme('auto');
      }
    });
  }

  return {
    captionPrompt, aggregationPrompt, chunk, nfmc, frameWidth, frameHeight,
    topk, topp, temp, maxTokens, seed, batch, RAG_batch, RAG_topk,
    S_TopP, S_TEMPERATURE, SMAX_TOKENS, C_TopP, C_TEMPERATURE, C_MAX_TOKENS,
    A_TopP, A_TEMPERATURE, A_MAX_TOKENS, enableAudio, theme, language
  };
});