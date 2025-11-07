<template>
  <!-- 메뉴 틀 -->
  <div id="video_list" class="w-[100%] h-[90%]">
    <header id="header" class="flex items-center justify-between">
      <div class="w-[500px] bg-blue-400 text-white text-lg p-3 text-center rounded-lg shadow-md mt-6 ml-12">
        <p>My Video Storage</p>
      </div>
      <div class="flex items-center h-12 mr-12 mt-auto ml-auto">
        <label
          class="bg-blue-400 hover:bg-blue-600 text-white px-4 py-2 rounded-lg shadow cursor-pointer flex items-center">
          <span>Upload Video</span>
          <input type="file" accept="video/*" multiple class="hidden" @change="handleUpload" />
        </label>
      </div>
    </header>
    <!-- 비디오 리스트 -->
    <div id="list" class="w-full h-full border-[1px] border-black bg-gray-300 rounded-[12px] p-6 mt-6">
      <div class="w-[100%] h-[90%] border-[1px] border-black bg-white rounded-[12px]">
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6 p-6">
          <div v-for="video in items" :key="video.id"
            class="flex flex-col items-center justify-center bg-gray-100 rounded-lg shadow hover:bg-blue-100 cursor-pointer p-3 border border-gray-300"
            @click="toggleSelect(video.id)">
            <div class="w-[100%] h-[100%] flex items-center justify-center bg-gray-300 rounded mb-2 overflow-hidden relative">
              <input type="checkbox" class="absolute top-1 left-1 z-10" v-model="selectedIds" :value="video.id" />
              <video v-if="video.url" :src="video.url" class="object-cover rounded" controls preload="metadata"></video>
              <span v-else class="text-gray-400">No Thumbnail</span>
              <div v-if="video.title" class="absolute bottom-0 left-0 w-full bg-black bg-opacity-60 text-white text-xs px-1 py-0.5 truncate text-center pointer-events-none">
                {{ video.title }}
              </div>
            </div>
            <div class="flex gap-2 mt-1">
              <button @click="openItem(video)" class="text-blue-500 hover:underline text-xs">열기</button>
            </div>
          </div>
        </div>
      </div>
      <!-- 우측 하단 선택 동영상 삭제 버튼 -->
      <div class="fixed bottom-[110px] right-[80px] z-50">
        <button
          class="px-5 py-3 rounded-lg bg-red-500 text-white shadow-lg hover:bg-red-600"
          :disabled="selectedIds.length === 0"
          @click="showDeletePopup = true"
        >
          선택 동영상 삭제 ({{ selectedIds.length }})
        </button>
      </div>

      <!-- 중앙 팝업창 -->
      <div v-if="showDeletePopup" class="fixed inset-0 flex items-center justify-center z-[100] bg-black bg-opacity-40">
        <div class="bg-white rounded-xl shadow-xl p-8 min-w-[350px] max-w-[90vw] relative">
          <div class="text-lg font-semibold mb-4 text-center">
            {{ selectedIds.length }}개의 동영상이 삭제됩니다.<br>진행하시겠습니까?
          </div>
          <div class="flex justify-end gap-3 mt-8">
            <button class="px-5 py-2 rounded-lg bg-red-500 text-white hover:bg-red-600" @click="confirmDelete">delete</button>
            <button class="px-5 py-2 rounded-lg bg-gray-300 text-black hover:bg-gray-400" @click="showDeletePopup = false">cancel</button>
          </div>
        </div>
      </div>

      <!-- 좌측 하단 Summary, Search 버튼 -->
      <div class="fixed bottom-[110px] left-[290px] z-50 flex gap-4">
        <button
          class="w-[200px] text-[18px] px-5 py-3 rounded-lg bg-blue-500 text-white shadow-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:text-white"
          :disabled="selectedIds.length === 0"
          @click="goToSummary"
        >Summary</button>
        <button
          class="w-[200px] text-[18px] px-5 py-3 rounded-lg bg-green-500 text-white shadow-lg hover:bg-green-600 disabled:bg-gray-400 disabled:text-white"
          :disabled="selectedIds.length === 0"
        >Search</button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from 'vue-router';
const router = useRouter();
const showDeletePopup = ref(false);
function toggleSelect(id) {
  const idx = selectedIds.value.indexOf(id);
  if (idx === -1) {
    selectedIds.value.push(id);
  } else {
    selectedIds.value.splice(idx, 1);
  }
}

const items = ref([]);
const selectedIds = ref([]);

// 페이지 로드 시 localStorage에서 동영상 목록 불러오기
if (localStorage.getItem("videoItems")) {
  items.value = JSON.parse(localStorage.getItem("videoItems"));
}

async function handleUpload(e) {
  const files = Array.from(e.target.files ?? []);
  if (!files.length) return;
  for (const file of files) {
    if (!file.type.startsWith('video/')) {
      alert('동영상 파일만 업로드할 수 있습니다.');
      continue;
    }
    // 동영상 미리보기 URL 생성
    const url = URL.createObjectURL(file);
    const video = {
      id: Date.now() + Math.random(),
      title: file.name,
      url,
      date: new Date().toISOString().slice(0, 10),
      summary: ""
    };
    items.value.unshift(video);
  }
  localStorage.setItem("videoItems", JSON.stringify(items.value));
}

function confirmDelete() {
  items.value = items.value.filter(v => !selectedIds.value.includes(v.id));
  localStorage.setItem("videoItems", JSON.stringify(items.value));
  selectedIds.value = [];
  showDeletePopup.value = false;
}

function goToSummary() {
  const selectedVideos = items.value.filter(v => selectedIds.value.includes(v.id));
  localStorage.setItem('summarySelectedVideos', JSON.stringify(selectedVideos));
  router.push({ name: 'Summary' });
}
</script>
