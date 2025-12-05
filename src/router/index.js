/***************************************************
 * src/router/index.js
 **************************************************/
import { createRouter, createWebHistory } from "vue-router";

import Summarize from "@/pages/Summarize.vue";
import search from "@/pages/Search.vue"; // 파일명 유지, 변수명/라우트명 카멜/파스칼 통일
import Report from "@/pages/Report.vue";
import Setting from "@/pages/Setting.vue";
import Login from "@/pages/Login.vue";
import Register from "@/pages/Register.vue";

const routes = [
  { path: "/", redirect: "/login" },
  { path: "/summarize", name: "Summarize", component: Summarize },
  { path: "/search", name: "search", component: search },
  { path: "/report", name: "Report", component: Report },
  { path: "/setting", name: "Setting", component: Setting },
  { path: "/login", name: "Login", component: Login },
  { path: "/register", name: "Register", component: Register }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// 네비게이션 가드: 로그인된 사용자는 자동으로 /search로 리다이렉트
router.beforeEach((to, from, next) => {
  const userId = localStorage.getItem("vss_user_id");
  
  // 로그인 페이지로 가려고 할 때 이미 로그인되어 있으면 /search로 리다이렉트
  if (to.path === "/login" && userId) {
    next("/search");
  }
  // 회원가입 페이지는 로그인 여부와 관계없이 접근 가능
  else if (to.path === "/register") {
    next();
  }
  // 보호된 페이지(로그인이 필요한 페이지)에 접근할 때
  else if (to.path !== "/login" && to.path !== "/register" && !userId) {
    next("/login");
  }
  else {
    next();
  }
});

export default router;
