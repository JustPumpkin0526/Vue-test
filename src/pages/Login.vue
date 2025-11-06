<template>
  <div class="max-w-md mx-auto rounded-2xl border p-6 bg-gray-50">
    <h2 class="text-xl font-semibold mb-4">로그인</h2>

    <label class="block text-sm mb-1">ID</label>
    <input v-model="id" class="w-full border rounded-md px-3 py-2 mb-3" />

    <label class="block text-sm mb-1">비밀번호</label>
    <input v-model="pw" type="password" class="w-full border rounded-md px-3 py-2 mb-4" />

    <div class="flex items-center justify-between">
      <button class="text-sm text-vix-primary" @click="resetPw">비밀번호 재설정</button>
      <div class="space-x-2">
        <router-link class="text-sm" to="/register">회원가입</router-link>
        <button class="px-4 py-2 rounded-md bg-vix-primary text-white" @click="login">로그인</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import axios from "axios";

const router = useRouter();
const id = ref("");
const pw = ref("");

async function login() {
  try {
    const res = await axios.post("http://localhost:8100/login", {
      username: id.value,
      password: pw.value
    });
    if (res.data && res.data.success) {
      // 로그인 성공 시
      localStorage.setItem("vss_user_id", id.value);
      window.dispatchEvent(new Event("vss-login"));
      router.push("/Video_List");
    } else {
      alert(res.data.message || "가입되지 않았거나 비밀번호가 올바르지 않습니다.");
    }
  } catch (err) {
    if (err.response && err.response.data && err.response.data.detail) {
      alert(err.response.data.detail);
    } else {
      alert("로그인 중 오류가 발생했습니다.");
    }
  }
}
function resetPw() {
  alert("사용자 인증 후 비밀번호 재설정 진행");
}
</script>
