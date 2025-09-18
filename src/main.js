import { createApp } from 'vue'
import App from './App.vue'
import './index.css'   // ✅ TailwindCSS 적용
import menu_router from './router/menu';

createApp(App).use(menu_router).mount('#app');
