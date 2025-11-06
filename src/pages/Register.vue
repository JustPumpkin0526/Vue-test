<template>
  <div class="max-w-md mx-auto rounded-2xl border p-6 bg-gray-50">
    <h2 class="text-xl font-semibold mb-4">회원 가입</h2>

    <label class="block text-sm mb-1">사용할 ID</label>
    <input v-model="id" class="w-full border rounded-md px-3 py-2 mb-3" />

    <label class="block text-sm mb-1">비밀번호 (영문/숫자/특수문자 포함 8자 이상)</label>
    <input v-model="pw" type="password" class="w-full border rounded-md px-3 py-2 mb-3" />

    <label class="block text-sm mb-1">Email</label>
    <input v-model="email" type="email" class="w-full border rounded-md px-3 py-2 mb-4" />

    <div class="flex items-center gap-2">
      <button class="px-3 py-2 rounded-md bg-gray-100" :disabled="sent" @click="sendCode">
        보안 코드 전송
      </button>
      <button class="px-3 py-2 rounded-md bg-gray-100" :disabled="sent" @click="resend">
        재전송(30초 후)
      </button>
    </div>

    <label class="block text-sm mt-4 mb-1">보안 코드</label>
    <input v-model="code" class="w-full border rounded-md px-3 py-2 mb-4" />

    <div class="flex items-center justify-between">
      <router-link class="text-sm" to="/login">로그인으로 가기</router-link>
      <button class="px-4 py-2 rounded-md bg-vix-primary text-white" @click="register">회원 가입</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import axios from "axios";

const id = ref("");
const pw = ref("");
const email = ref("");
const code = ref("");
const sent = ref(false);

function sendCode() {
  sent.value = true;
  setTimeout(() => (sent.value = false), 30000);
  alert(`보안 코드가 ${email.value}로 전송되었습니다.`);
}
function resend() { alert("30초 이후 활성화됩니다."); }

async function register() {
  try {
    const res = await axios.post("http://localhost:8100/register", {
      username: id.value,
      password: pw.value,
      email: email.value
    });
    alert(res.data.message || "가입 완료");
    id.value = "";
    pw.value = "";
    email.value = "";
    code.value = "";
  } catch (err) {
    if (err.response && err.response.data && err.response.data.detail) {
      alert(err.response.data.detail);
    } else {
      alert("회원가입 중 오류가 발생했습니다.");
    }
  }
}
</script>
