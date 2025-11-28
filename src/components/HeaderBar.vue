<template>
  <header class="w-full border-b bg-gray-50">
    <div class="px-4 py-3 flex items-center justify-between">
      <div class="flex items-center gap-3 cursor-pointer" @click="goToVideoList">
        <img :src="logoUrl" alt="Intellivix Logo" class="h-8 w-auto object-contain" />
        <h1 class="text-2xl font-bold text-vix-primary">Vix VSS</h1>
      </div>
      <nav class="flex gap-4 items-center">
        <template v-if="userId">
          <span class="text-sm text-gray-700 font-semibold">{{ userId }}님</span>
          <button class="text-sm text-gray-500 hover:text-vix-primary" @click="logout">로그아웃</button>
        </template>
        <template v-else>
          <router-link class="text-sm text-gray-600 hover:text-vix-primary" to="/login">Sign in</router-link>
          <router-link class="text-sm text-gray-600 hover:text-vix-primary" to="/register">Sign up</router-link>
        </template>
      </nav>
    </div>
  </header>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import logoUrl from '@/assets/icons/Intellivix_logo.png';

const userId = ref("");
const router = useRouter();

function checkLogin() {
  userId.value = localStorage.getItem("vss_user_id") || "";
}

function logout() {
  localStorage.removeItem("vss_user_id");
  userId.value = "";
  window.dispatchEvent(new Event("vss-login"));
  router.push("/login");
}

function goToVideoList() {
  router.push("/video_storage");
}

onMounted(() => {
  checkLogin();
  window.addEventListener("storage", checkLogin);
  window.addEventListener("vss-login", checkLogin);
});
</script>