<template>
  <div class="min-h-screen flex flex-col bg-white">
    <!-- Header -->
    <HeaderBar />

    <div class="flex flex-1 overflow-hidden">
      <!-- Sidebar -->
      <SidebarNav class="hidden md:flex"/>

      <!-- Router View -->
      <main class="flex-1 p-4 md:p-6 overflow-auto">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import HeaderBar from "@/components/HeaderBar.vue";
import SidebarNav from "@/components/SidebarNav.vue";
</script>
