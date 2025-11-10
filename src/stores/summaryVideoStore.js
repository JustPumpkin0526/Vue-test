import { defineStore } from 'pinia';

export const useSummaryVideoStore = defineStore('summaryVideo', {
  state: () => ({
    videos: []
  }),
  actions: {
    setVideos(videos) {
      this.videos = videos;
    },
    clearVideos() {
      this.videos = [];
    }
  }
});
