import { createRouter, createWebHistory } from 'vue-router';
import HomePage from '../components/video_summarization.vue';
import AboutPage from '../components/router_test.vue';
import ContactPage from '../components/Vue-test.vue';

const routes = [
  { path: '/', component: HomePage },
  { path: '/about', component: AboutPage },
  { path: '/contact', component: ContactPage },
];

const menu_router = createRouter({
  history: createWebHistory(),
  routes,
});

export default menu_router;
