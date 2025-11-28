/***************************************************
 * src/router/index.js
 **************************************************/
import { createRouter, createWebHistory } from "vue-router";

import Summarize from "@/pages/Summarize.vue";
import VideoStorage from "@/pages/Video_Storage.vue"; // 파일명 유지, 변수명/라우트명 카멜/파스칼 통일
import Report from "@/pages/Report.vue";
import Setting from "@/pages/Setting.vue";
import Login from "@/pages/Login.vue";
import Register from "@/pages/Register.vue";

const routes = [
  { path: "/", redirect: "/video_storage" },
  { path: "/summarize", name: "Summarize", component: Summarize },
  { path: "/video_storage", name: "VideoStorage", component: VideoStorage },
  { path: "/report", name: "Report", component: Report },
  { path: "/setting", name: "Setting", component: Setting },
  { path: "/login", name: "Login", component: Login },
  { path: "/register", name: "Register", component: Register }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
