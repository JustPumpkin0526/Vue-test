/***************************************************
 * src/router/index.js
 **************************************************/
import { createRouter, createWebHistory } from "vue-router";

import Summary from "@/pages/Summary.vue";
import Video_List from "@/pages/Video_List.vue";
import Report from "@/pages/Report.vue";
import Setting from "@/pages/Setting.vue";
import Login from "@/pages/Login.vue";
import Register from "@/pages/Register.vue";

const routes = [
  { path: "/", redirect: "/video_list" },
  { path: "/summary", component: Summary },
  { path: "/video_list", component: Video_List },
  { path: "/report", component: Report },
  { path: "/setting", component: Setting },
  { path: "/login", component: Login },
  { path: "/register", component: Register }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
