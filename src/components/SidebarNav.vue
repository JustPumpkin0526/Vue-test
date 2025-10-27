<template>
  <aside class="w-56 shrink-0 border-r bg-gray-100 p-4 flex flex-col justify-between">
    <nav class="space-y-2">
      <RouterLink
        to="/summary"
        class="block rounded-md px-3 py-2 hover:bg-white hover:shadow"
        :class="isActive('/summary')">
        Summary
      </RouterLink>
      <RouterLink
        to="/search"
        class="block rounded-md px-3 py-2 hover:bg-white hover:shadow"
        :class="isActive('/search')">
        Search
      </RouterLink>
      <RouterLink
        to="/report"
        class="block rounded-md px-3 py-2 hover:bg-white hover:shadow"
        :class="isActive('/report')">
        Report
      </RouterLink>
      <RouterLink
        to="/setting"
        class="block rounded-md px-3 py-2 hover:bg-white hover:shadow"
        :class="isActive('/setting')">
        Setting
      </RouterLink>
    </nav>

    <div class="space-y-2">
      <button class="w-full rounded-md px-3 py-2 bg-white hover:shadow text-left">Collapse</button>
    </div>
  </aside>
</template>

<script setup>
import { useRoute } from "vue-router";
const route = useRoute();
const isActive = (path) =>
  route.path.startsWith(path) ? "bg-white shadow text-vix-primary font-medium" : "text-gray-700";

import { ref } from "vue";
const activeTab = ref("summary");
</script>
