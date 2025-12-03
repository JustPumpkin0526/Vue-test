<template>
  <aside :class="[collapsed ? 'w-[105px]' : 'w-64', ' h-[95.65vh] shrink-0 border-r bg-gray-100 p-6 flex flex-col justify-between relative transition-all duration-200']">
    <nav class="flex flex-col flex-1">
      <RouterLink
        to="/search"
        class="flex items-center gap-3 rounded-md px-4 py-3 relative overflow-hidden transform transition-all duration-200 group hover:shadow hover:bg-white active:scale-[0.97]"
        :class="isActive('/search')">
        <svg viewBox="0 0 24 24" class="w-6 h-6 transition-transform duration-200 group-hover:scale-110 group-hover:rotate-3 icon-base">
          <circle cx="11" cy="11" r="7" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <span v-if="!collapsed" class="transition-opacity duration-200 text-lg">Search</span>
      </RouterLink>
      <RouterLink
        to="/summarize"
        class="flex items-center gap-3 rounded-md px-4 py-3 relative overflow-hidden transform transition-all duration-200 group hover:shadow hover:bg-white active:scale-[0.97]"
        :class="isActive('/summarize')">
        <svg viewBox="0 0 24 24" class="w-6 h-6 transition-transform duration-200 group-hover:scale-110 group-hover:rotate-3 icon-base">
          <rect x="3" y="4" width="18" height="16" rx="2" ry="2" />
          <line x1="7" y1="8" x2="17" y2="8" />
          <line x1="7" y1="12" x2="13" y2="12" />
          <line x1="7" y1="16" x2="11" y2="16" />
        </svg>
        <span v-if="!collapsed" class="transition-opacity duration-200 text-lg">Summarize</span>
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

      <div class="absolute left-6 right-6 bottom-[1vh] flex flex-col items-start space-y-3">
        <!-- Setting (PNG icon) -->
        <button
          type="button"
          :class="['w-full text-left', 'flex items-center gap-3 rounded-md px-4 py-3 relative overflow-hidden transform transition-all duration-200 group hover:shadow hover:bg-white active:scale-[0.97]']"
          title="Setting"
          @click.stop.prevent="() => {}"
        >
          <img src="@/assets/icons/setting.png" alt="Setting" class="w-6 h-6 object-contain" />
          <span v-if="!collapsed" class="transition-opacity duration-200 text-lg">Setting</span>
        </button>

        <!-- Help (question mark icon) -->
        <button
          type="button"
          :class="['w-full text-left', 'flex items-center gap-3 rounded-md px-4 py-3 relative overflow-hidden transform transition-all duration-200 group hover:shadow hover:bg-white active:scale-[0.97]']"
          title="Help"
          @click.stop.prevent="() => {}"
        >
          <svg viewBox="0 0 24 24" class="w-6 h-6 transition-transform duration-200 group-hover:scale-110 group-hover:rotate-3 icon-base text-gray-700">
            <path d="M12 18h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M9.09 9a3 3 0 115.82 0c0 2-3 2.5-3 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1" fill="none" />
          </svg>
          <span v-if="!collapsed" class="transition-opacity duration-200 text-lg">Help</span>
        </button>

        <!-- Collapse button positioned with the bottom group -->
        <button
          :class="['w-full text-center bg-white', 'items-center gap-3 rounded-md px-4 py-3 relative overflow-hidden transform transition-all duration-200 group hover:shadow active:scale-[0.97]']"
          @click="toggleCollapse"
          aria-label="Toggle sidebar"
          :aria-expanded="(!collapsed).toString()"
        >
          <span class="transition-opacity duration-200 select-none text-lg">{{ collapsed ? '>>' : '<<' }}</span>
        </button>
      </div>
    </nav>
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
