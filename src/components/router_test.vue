<template>
  <div>
    <nav>
      <button @click="currentMenu = 'home'">Home</button>
      <button @click="currentMenu = 'about'">About</button>
    </nav>

    <HomePage v-if="currentMenu === 'home'" />
    <AboutPage v-if="currentMenu === 'about'" />
  </div>
</template>

