/***************************************************
 * src/services/api.js
 * 실제 API 연동 전까지 데모 동작을 위한 모의 함수
 **************************************************/
export default {
  async runVssInference({ fileName }) {
    // 실제로는 백엔드에 업로드/추론 요청
    return new Promise((resolve) =>
      setTimeout(() => resolve({
        summary:
`[00:00–00:45] The white car accelerates and weaves through traffic.
[00:45–02:00] Two police vehicles engage pursuit as the suspect changes lanes rapidly.
[02:00–03:00] The vehicle exits and slows near an intersection; officers close in.`
      }), 600)
    );
  },

  async askAboutResult({ question, context }) {
    return new Promise((resolve) =>
      setTimeout(() => resolve({
        answer: `요약에 따르면, 해당 질문("${question}")과 관련된 이벤트는 00:45–02:00 구간에서 관찰됩니다.`
      }), 300)
    );
  },

  saveSummary({ content }) {
    console.log("Saved summary:", content.slice(0, 80), "...");
  },

  searchVideos({ q, filter, page }) {
    const items = Array.from({ length: 6 }).map((_, i) => ({
      id: `${page}-${i}`,
      title: `캡처 영상 #${(page - 1) * 6 + i + 1}${q ? ` (${q})` : ""}`,
      date: "2025-10-27"
    }));
    return { items, pages: 5 };
  },

  listReports({ page }) {
    const items = Array.from({ length: 6 }).map((_, i) => ({
      id: `${page}-${i}`,
      title: `리포트 #${(page - 1) * 6 + i + 1}`,
      content:
`# Report ${(page - 1) * 6 + i + 1}
- Summary blocks
- Q&A
- Attachments`
    }));
    return { items, pages: 3 };
  },

  saveSetting(payload) { console.log("Saved settings:", payload); },
  login({ id, pw }) { return !!(id && pw && pw.length >= 4); },
  register({ id, pw, email, code }) {
    const pwOk = /(?=.*[A-Za-z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}/.test(pw || "");
    return !!(id && pwOk && email && code);
  }
};
