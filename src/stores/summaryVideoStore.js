import { defineStore } from 'pinia';

// 동영상 객체 타입 예시:
// {
//   id: number,
//   title: string,
//   url: string,
//   date: string,
//   file?: File // File 객체가 포함될 수 있음
// }

export const useSummaryVideoStore = defineStore('summaryVideo', {
  state: () => ({
    /**
     * @type {Array<{id: number, title: string, url: string, date: string, file?: File}>}
     */
    videos: []
  }),
  actions: {
    /**
     * File 객체가 포함된 동영상 배열을 저장
     * @param {Array<{id: number, title: string, url: string, date: string, file?: File}>} videos
     */
    setVideos(videos) {
      this.videos = videos.map(v => ({
        id: v.id,
        title: v.title,
        originUrl: v.originUrl,
        displayUrl: v.displayUrl,
        objectUrl: v.objectUrl,
        date: v.date,
        file: v.file instanceof File ? v.file : null,
        url: v.url, // videoUrl이 url로 저장됨
        summary: v.summary || '' // Ensure summary is included
      }));
    },
    clearVideos() {
      this.videos = [];
    }
  }
});
