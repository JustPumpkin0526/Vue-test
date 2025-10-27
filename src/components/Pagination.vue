<template>
  <div class="flex items-center justify-center gap-2">
    <button class="px-3 py-1 rounded bg-gray-100" :disabled="page<=1" @click="$emit('update:page', page-1)">〈</button>
    <span class="text-sm text-gray-600">Page {{ page }} / {{ pages }}</span>
    <button class="px-3 py-1 rounded bg-gray-100" :disabled="page>=pages" @click="$emit('update:page', page+1)">〉</button>
  </div>
</template>

<script setup>
defineProps({
  page: { type: Number, default: 1 },
  pages: { type: Number, default: 1 }
});
</script>
