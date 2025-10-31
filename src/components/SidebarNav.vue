<template>
  <aside :class="[collapsed ? 'w-18 text-center' : 'w-56', 'shrink-0 border-r bg-gray-100 p-4 flex flex-col justify-between transition-all duration-200']">
    <nav class="space-y-2">
      <RouterLink
        to="/video_list"
        class="block rounded-md px-3 py-2 hover:bg-white hover:shadow"
        :class="isActive('/video_list')">
        {{collapsed ? '🔎' : 'Video List'}}
      </RouterLink>
      <RouterLink
        to="/summary"
        class="block rounded-md px-3 py-2 hover:bg-white hover:shadow"
        :class="isActive('/summary')">
        {{collapsed ? '✦' : 'Summary'}}
      </RouterLink>
      <RouterLink
        to="/report"
        class="block rounded-md px-3 py-2 hover:bg-white hover:shadow"
        :class="isActive('/report')">
        {{collapsed ? '📄' : 'Report'}}
      </RouterLink>
      <RouterLink
        to="/setting"
        class="block rounded-md px-3 py-2 hover:bg-white hover:shadow"
        :class="isActive('/setting')">
        {{collapsed ? '⚙' : 'Setting'}}
      </RouterLink>
    </nav>

    <div class="space-y-2 flex flex-col items-center">
      <button :class="[collapsed ? 'text-center' : 'w-full', 'rounded-md px-3 py-2 bg-white hover:shadow text-left ml-auto']" @click="toggleCollapse">
        {{ collapsed ? '>>' : 'Collapse' }}
      </button>
    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue';
import { useRoute } from "vue-router";
const route = useRoute();
const isActive = (path) =>
  route.path.startsWith(path) ? "bg-white shadow text-vix-primary font-medium" : "text-gray-700";

const collapsed = ref(false);
function toggleCollapse() {
  collapsed.value = !collapsed.value;
}
</script>
