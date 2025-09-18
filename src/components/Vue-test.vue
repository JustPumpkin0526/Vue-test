<template>
  <header>
    <img src="https://i.namu.wiki/i/R_osaEdMT8LXai9Lwdgpr8_DIH5k0sD_V05Hcx-n2NgFeGeDEhCV7tq00fQNUrlsmvD55287ZDye13FWR2lqIiGOShvOojLDNzWN0ck0a_5UO19pxRCz34HI603DaKxC7pwifKpk0rtWBpzUDKJxYQ.webp" alt="logo"></img>
    <h1>| VIDEO SEARCH AND SUMMARIZATION</h1>
  </header>
  <div>
    <nav class="menu">
      <!-- 라우터 링크 대신 버튼 모양으로 -->
      <button
        v-for="item in items"
        :key="item.path"
        class="menu-button"
        :class="{ active: $route.path === item.path }"
        @click="$router.push(item.path)"
      >
        {{ item.label }}
      </button>
    </nav>

    <!-- 라우터 화면 -->
    <router-view />
  </div>
</template>

<script>
export default {
  data() {
    return {
      items: [
        { path: '/', label: 'VIDEO FILE SUMMARIZATION & Q&A' },
        { path: '/about', label: 'LIVE STREAM SUMMARIZATION' },
        { path: '/contact', label: 'IMAGE FILE SUMMARIZATION & Q&A' },
      ],
    };
  },
};
</script>

<style scoped>
/* 메뉴 바 */
.menu {
  display: flex;
  gap: 40px;          /* 버튼 간격 넓히기 */
  justify-content: left;
  padding: 20px;
  background: #f5f5f5;
  position: relative; /* ::after 사용 가능 */
}

/* 메뉴 바로 아래 실선 (::after) */
.menu::after {
  content: "";
  position: absolute;
  bottom: 0;       /* 메뉴 바로 아래 */
  left: 0;
  width: 100%;
  height: 2px;     /* 선 두께 */
  background-color: #ccc; /* 선 색상 */
}


/* 버튼 기본 */
.menu-button {
  background: none;
  border: none;
  font: inherit;
  cursor: pointer;
  padding: 6px 0;
  position: relative;
  color: #333; /* 기본 글자색 */
  transition: color 0.3s ease; /* 색상 전환 애니메이션 */
}

/* hover 시 */
.menu-button:hover {
  color: #000;
}

/* 밑줄 애니메이션 */
.menu-button::after {
  content: "";
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 100%;
  height: 2px;
  background: darkblue;       /* 밑줄 색도 lightblue */
  transform: scaleX(0);
  transform-origin: center;
  transition: transform 0.3s ease;
}

/* ✅ 현재 활성화된 버튼 */
.menu-button.active {
  color: darkblue; /* 글자 색상 변경 */
}

.menu-button.active::after {
  transform: scaleX(1);
}

</style>