<template>
  <aside :class="[collapsed ? 'w-[105px] text-center' : 'w-64', 'shrink-0 border-r bg-gray-100 p-6 flex flex-col justify-between transition-all duration-200']">
    <nav class="space-y-3">
      <RouterLink
        to="/video_storage"
        class="flex items-center gap-3 rounded-md px-4 py-3 relative overflow-hidden transform transition-all duration-200 group hover:shadow hover:bg-white active:scale-[0.97]"
        :class="isActive('/video_storage')">
        <svg viewBox="0 0 24 24" class="w-6 h-6 transition-transform duration-200 group-hover:scale-110 group-hover:rotate-3 icon-base">
          <circle cx="11" cy="11" r="7" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <span v-if="!collapsed" class="transition-opacity duration-200 text-lg">Video Storage</span>
      </RouterLink>
      <RouterLink
        to="/summary"
        class="flex items-center gap-3 rounded-md px-4 py-3 relative overflow-hidden transform transition-all duration-200 group hover:shadow hover:bg-white active:scale-[0.97]"
        :class="isActive('/summary')">
        <svg viewBox="0 0 24 24" class="w-6 h-6 transition-transform duration-200 group-hover:scale-110 group-hover:rotate-3 icon-base">
          <rect x="3" y="4" width="18" height="16" rx="2" ry="2" />
          <line x1="7" y1="8" x2="17" y2="8" />
          <line x1="7" y1="12" x2="13" y2="12" />
          <line x1="7" y1="16" x2="11" y2="16" />
        </svg>
        <span v-if="!collapsed" class="transition-opacity duration-200 text-base">Summary & Query</span>
      </RouterLink>
      <RouterLink
        to="/report"
        class="flex items-center gap-3 rounded-md px-4 py-3 relative overflow-hidden transform transition-all duration-200 group hover:shadow hover:bg-white active:scale-[0.97]"
        :class="isActive('/report')">
        <svg viewBox="0 0 24 24" class="w-6 h-6 transition-transform duration-200 group-hover:scale-110 group-hover:rotate-3 icon-base">
          <path d="M4 19V5a2 2 0 0 1 2-2h8l6 6v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z" />
          <polyline points="14 3 14 8 19 8" />
          <line x1="8" y1="13" x2="16" y2="13" />
          <line x1="8" y1="17" x2="12" y2="17" />
        </svg>
        <span v-if="!collapsed" class="transition-opacity duration-200 text-lg">Report</span>
      </RouterLink>
      <RouterLink
        to="/setting"
        class="flex items-center gap-3 rounded-md px-4 py-3 relative overflow-hidden transform transition-all duration-200 group hover:shadow hover:bg-white active:scale-[0.97]"
        :class="isActive('/setting')">
        <img :src="settingIcon" alt="Setting" class="w-6 h-6 transition-transform duration-200 group-hover:scale-110 group-hover:rotate-3" :class="route.path.startsWith('/setting') ? 'png-active' : ''" />
        <span v-if="!collapsed" class="transition-opacity duration-200 text-lg">Setting</span>
      </RouterLink>
    </nav>

    <div class="space-y-3 flex flex-col items-center">
      <button
        :class="[collapsed ? 'text-center' : 'w-full text-left', 'flex items-center gap-3 rounded-md px-4 py-3 relative overflow-hidden transform transition-all duration-200 group bg-white hover:shadow hover:bg-white active:scale-[0.97]']"
        @click="toggleCollapse"
        aria-label="Toggle sidebar"
        :aria-expanded="(!collapsed).toString()"
      >
        <span class="transition-opacity duration-200 select-none text-lg">{{ collapsed ? '>>' : 'Collapse' }}</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue';
import { useRoute } from "vue-router";
const route = useRoute();
const isActive = (path) =>
  route.path.startsWith(path)
    ? "text-vix-primary font-medium bg-gradient-to-r from-white to-vix-primary/10 shadow ring-1 ring-vix-primary/30"
    : "text-gray-700 hover:bg-gradient-to-r hover:from-white hover:to-gray-50";

// 인라인 SVG 사용으로 stroke=currentColor 적용. PNG는 필터 처리.
import settingIcon from '@/assets/icons/setting.png';
const collapsed = ref(false);
function toggleCollapse() {
  collapsed.value = !collapsed.value;
}
</script>

<style scoped>
/* Optional subtle fade-slide for future label transitions */
.fade-slide-enter-active, .fade-slide-leave-active { transition: all .2s ease; }
.fade-slide-enter-from, .fade-slide-leave-to { opacity:0; transform: translateX(-4px); }
.fade-slide-enter-to, .fade-slide-leave-from { opacity:1; transform: translateX(0); }
/* 인라인 SVG 공통 스타일 */
.icon-base {
  stroke: currentColor;
  fill: none;
  width: 1.5rem; /* Fixed size */
  height: 1.5rem; /* Fixed size */
}
/* 설정 PNG 활성시 파란색 계열 필터 */
.png-active { filter: brightness(0) saturate(100%) invert(32%) sepia(82%) saturate(1820%) hue-rotate(191deg) brightness(95%) contrast(94%); }
</style>
