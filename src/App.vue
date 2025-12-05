<template>
  <div class="min-h-screen flex flex-col bg-white">
    <!-- Header - 로그인/회원가입 페이지에서는 숨김 -->
    <HeaderBar v-if="!isAuthPage" />

    <div class="flex flex-1 overflow-hidden">
      <!-- Sidebar - 로그인/회원가입 페이지에서는 숨김 -->
      <SidebarNav v-if="!isAuthPage" class="hidden md:flex"/>

      <!-- Router View -->
      <main class="flex-1 overflow-auto" :class="{ 'w-full': isAuthPage }">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import HeaderBar from "@/components/HeaderBar.vue";
import SidebarNav from "@/components/SidebarNav.vue";
import './assets/tailwind.css';

const route = useRoute();

// 로그인/회원가입 페이지인지 확인
const isAuthPage = computed(() => {
  return route.path === '/login' || route.path === '/register';
});
</script>
