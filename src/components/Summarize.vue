<template>
  <div class="w-full min-h-screen bg-gradient-to-br from-gray-200 to-gray-300 via-gray-100 dark:from-gray-950 dark:to-gray-900 dark:via-gray-950 p-10">
    <div class="grid lg:grid-cols-2 gap-6">
      <!-- 좌측: 비디오/업로드 -->
      <section
        class="rounded-2xl p-5 bg-gradient-to-br from-white via-gray-50 to-gray-100 dark:from-gray-950 dark:via-gray-950 dark:to-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm hover:shadow-md transition-shadow duration-300">
        <!-- 헤더 -->
        <header class="flex items-center justify-between px-1 pb-3 mb-3 border-b border-slate-800/70 dark:border-gray-200/30">
          <!-- 좌측: 타이틀 / 설명 -->
          <div class="flex flex-col gap-1">
            <div
              class="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 dark:bg-emerald-500/20 border border-emerald-400/40 dark:border-emerald-400/60 w-fit">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span class="text-[11px] font-semibold tracking-wide text-emerald-600 dark:text-emerald-400 uppercase">
                {{ tSummarize.workspace }}
              </span>
            </div>
            <p class="text-xs md:text-sm text-black dark:text-gray-200 mt-1">
              {{ isZoomed ? (videoFiles[zoomedIndex]?.name || tSummarize.videoSection) : (videoFiles.length > 1 ? tSummarize.videoSection : (videoFiles[0]?.name || tSummarize.videoSection)) }}
              <span class="hidden md:inline">{{ tSummarize.adjustPerformance }}</span>
            </p>
          </div>
          <!-- 우측: 설정 버튼 -->
          <button @click="showSettingModal = true" :title="tSummarize.setting"
            class="w-9 h-9 flex items-center justify-center bg-slate-200/70 dark:bg-gray-700 hover:bg-slate-400/80 dark:hover:bg-gray-600 border border-slate-500/60 dark:border-gray-600 text-slate-100 dark:text-gray-200 backdrop-blur-md rounded-full shadow transition-all duration-200">
            <img :src="settingIcon" alt="설정" class="w-5 h-5 object-contain dark:brightness-0 dark:invert" />
          </button>
        </header>


        <!-- 비디오 리스트 / 업로드 영역 -->
        <div
          class="relative w-full border border-slate-200/80 dark:border-gray-800 bg-blue-100 dark:bg-blue-900/30 rounded-3xl p-6 mt-4 mb-4 shadow-[0_18px_45px_rgba(15,23,42,0.25)] backdrop-blur-md">
          <div
            class="aspect-video h-92 rounded-xl mb-3 flex items-center justify-center text-gray-600 dark:text-gray-400 transition-all cursor-pointer relative overflow-hidden group ring-1 ring-gray-300 dark:ring-gray-600"
            :class="[isDragging ? 'bg-blue-50 dark:bg-blue-900/50 ring-blue-300 dark:ring-blue-600' : 'bg-gray-200 dark:bg-gray-700']" @dragover.prevent="onDragOver"
            @dragleave.prevent="onDragLeave" @drop.prevent="onDrop" @click="onVideoAreaClick">
            <template v-if="!videoFiles || videoFiles.length === 0">
              <div v-if="streaming === false && sampleVideoPath"
                class="relative w-full h-full overflow-hidden rounded-xl bg-black">
                <!-- 샘플 동영상 (블러 없이 전체 영역 재생) -->
                <video ref="sampleVideoRef" :src="sampleVideoPath" class="w-full h-full object-cover brightness-75"
                  autoplay loop muted playsinline preload="auto"></video>
                <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <span v-if="!isDragging" class="font-bold text-white drop-shadow-lg text-center px-4">
                    {{ tSummarize.dropVideo }}<br />{{ tSummarize.or }}<br />{{ tSummarize.clickUpload }}
                  </span>
                  <span v-else class="text-white font-bold drop-shadow-lg">{{ tSummarize.dropHere }}</span>
                </div>
              </div>
              <span v-else-if="!isDragging"
                class="font-bold text-blue-500 dark:text-blue-400 flex flex-col items-center justify-center text-center w-full">
                {{ tSummarize.dropVideo }}<br>{{ tSummarize.or }}<br>{{ tSummarize.clickUpload }}
              </span>
              <span v-else class="text-blue-600 dark:text-blue-400 font-bold">{{ tSummarize.dropHere }}</span>
            </template>
            <template v-else-if="videoFiles.length === 1">
              <div class="relative w-full h-full" @mouseenter="singleVideo && (hoveredVideoId = singleVideo.id)"
                @mouseleave="hoveredVideoId = null">
                <!-- 지원하지 않는 형식이고 변환 중이거나 변환되지 않은 경우 -->
                <div v-if="singleVideo && isUnsupportedFormat(singleVideo.name || singleVideo.title || '') && (singleVideo._isConverting || !singleVideo.displayUrl?.includes('converted-videos'))" 
                  class="w-full h-full flex flex-col items-center justify-center bg-gray-200 dark:bg-gray-700 rounded-xl">
                  <div v-if="singleVideo._isConverting" class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-600 dark:border-gray-400 mb-2"></div>
                  <svg v-else class="w-12 h-12 text-gray-400 dark:text-gray-500 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  <span class="text-xs text-gray-500 dark:text-gray-400 text-center px-2">
                    {{ singleVideo._isConverting 
                      ? (settingStore.language === 'ko' ? '변환 중...' : 'Converting...')
                      : (settingStore.language === 'ko' ? '변환 대기 중...' : 'Waiting for conversion...')
                    }}
                  </span>
                </div>
                <!-- 비디오 엘리먼트 표시 (변환된 MP4 또는 지원하는 형식) -->
                <video v-else-if="singleVideo && singleVideo.displayUrl && (!isUnsupportedFormat(singleVideo.name || singleVideo.title || '') || singleVideo.displayUrl?.includes('converted-videos'))"
                  :src="singleVideo.displayUrl"
                  class="w-full h-full rounded-xl object-cover transition-opacity duration-300" preload="metadata"
                  :ref="el => { if (el && singleVideo) videoRefs[singleVideo.id] = el }"
                  @timeupdate="updateProgress(singleVideo.id, $event)"
                  @loadedmetadata="onVideoMetadataLoaded(singleVideo.id, $event)"
                  @ended="singleVideo && onVideoEnded(singleVideo.id)"
                  :class="{ 'brightness-75': !playingVideoIds.includes(singleVideo.id) }"></video>
                <!-- 정지 시 어두운 오버레이 -->
                <div v-if="singleVideo" class="absolute inset-0 pointer-events-none transition-colors duration-300"
                  :class="playingVideoIds.includes(singleVideo.id) ? 'bg-transparent' : 'bg-black/20'"></div>
                <!-- 재생하지 않은 동영상의 영상 길이 표시 (우측 하단) -->
                <div v-if="singleVideo && !playingVideoIds.includes(singleVideo.id) && durationMap[singleVideo.id]"
                  class="absolute bottom-2 right-2 px-2 py-1 bg-black/70 backdrop-blur-sm text-white text-xs font-medium rounded pointer-events-none">
                  {{ formatTime(durationMap[singleVideo.id]) }}
                </div>
                <!-- 하단 오버레이 진행바 & 시간 (재생 중일 때만 표시) -->
                <div v-if="singleVideo && playingVideoIds.includes(singleVideo.id)"
                  class="absolute bottom-0 left-0 right-0 p-2 bg-black/30 backdrop-blur-sm rounded-b-xl transition-all duration-300 pointer-events-none"
                  :class="{
                    'opacity-100 translate-y-0': hoveredVideoId === singleVideo.id,
                    'opacity-0 translate-y-full': hoveredVideoId !== singleVideo.id
                  }">
                  <div class="flex flex-col gap-1">
                    <div
                      class="w-full h-2 bg-gray-300/70 rounded-full relative cursor-pointer pointer-events-auto overflow-visible"
                      @click.stop="seekVideo(singleVideo.id, $event)"
                      :ref="el => { if (el && singleVideo) progressBarRefs[singleVideo.id] = el }">
                      <div :class="[
                        'h-full bg-gradient-to-r from-emerald-500 to-emerald-600',
                        (isScrubbing && draggingVideoId === singleVideo.id)
                          ? 'transition-none'
                          : 'transition-[width] duration-150 ease-linear'
                      ]" :style="{ width: `${progress[singleVideo.id] || 0}%` }"></div>
                      <div
                        class="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white rounded-full border border-emerald-500 cursor-pointer shadow hover:shadow-md hover:scale-110 transition-all pointer-events-auto"
                        :style="{ left: `calc(${progress[singleVideo.id] || 0}% - 8px)` }"
                        @mousedown="startDragging(singleVideo.id, $event)" @click.stop></div>
                    </div>
                    <div
                      class="flex justify-between text-[10px] font-medium text-gray-200 tracking-wide px-1 pointer-events-auto">
                      <span>{{ formatTime(currentTimeMap[singleVideo.id] || 0) }}</span>
                      <span>{{ formatTime(durationMap[singleVideo.id] || 0) }}</span>
                    </div>
                  </div>
                </div>
                <button v-if="singleVideo" @click.stop="togglePlay(singleVideo.id)" :class="{
                  'opacity-100 scale-100': hoveredVideoId === singleVideo.id || !playingVideoIds.includes(singleVideo.id),
                  'opacity-0 scale-90': hoveredVideoId !== singleVideo.id && playingVideoIds.includes(singleVideo.id)
                }" class="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-black/60 to-black/40 backdrop-blur-sm text-white rounded-full w-14 h-14 m-auto transition-all duration-300 hover:scale-110 active:scale-95">
                  <svg v-if="!playingVideoIds.includes(singleVideo.id)" xmlns="http://www.w3.org/2000/svg"
                    fill="currentColor" viewBox="0 -0.5 16 16" class="w-10 h-10">
                    <path
                      d="M6.271 4.055a.5.5 0 0 1 .759-.429l4.592 3.11a.5.5 0 0 1 0 .828l-4.592 3.11a.5.5 0 0 1-.759-.429V4.055z" />
                  </svg>
                  <svg v-else xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 16 16"
                    class="w-10 h-10">
                    <path
                      d="M5.5 3.5A.5.5 0 0 1 6 3h1a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5H6a.5.5 0 0 1-.5-.5v-9zM9.5 3.5A.5.5 0 0 1 10 3h1a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-9z" />
                  </svg>
                </button>
              </div>
            </template>
            <template v-else>
              <!-- 여러 개일 때 리스트 & 확대 분기 -->
              <div v-if="!isZoomed" id="list" class="relative w-full h-full">
                <div
                  class="w-full h-[100%] border border-slate-200/80 dark:border-gray-800 bg-gray-50 dark:bg-gray-950 rounded-2xl overflow-y-auto shadow-inner">
                  <div class="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-3 gap-6 p-6">
                    <div v-for="(video, idx) in videoFiles" :key="video.id"
                      class="flex flex-col items-center justify-center rounded-2xl shadow-md hover:shadow-xl cursor-pointer p-3 border border-gray-200 dark:border-gray-700 relative transform transition-all duration-300 hover:scale-105 hover:-translate-y-1 group bg-white dark:bg-gray-800"
                      :class="{ 'ring-2 ring-blue-400 dark:ring-blue-500 bg-blue-100 dark:bg-blue-900/30': selectedIndexes.includes(video.id) }"
                      @click="selectVideo(video.id)" @contextmenu.prevent.stop="onVideoContextMenu(video, idx, $event)">
                      <div
                        class="flex items-center justify-center bg-gray-200 dark:bg-gray-700 rounded-xl overflow-hidden relative group"
                        @mouseenter="hoveredVideoId = video.id" @mouseleave="hoveredVideoId = null">
                        <input type="checkbox" class="absolute top-1 left-1 z-10" v-model="selectedIndexes"
                          :value="video.id" />
                        <!-- 지원하지 않는 형식이고 변환 중이거나 변환되지 않은 경우 -->
                        <div v-if="isUnsupportedFormat(video.name || video.title || '') && (video._isConverting || !video.displayUrl?.includes('converted-videos'))" 
                          class="w-full h-full flex flex-col items-center justify-center bg-gray-200 dark:bg-gray-700 rounded-xl">
                          <div v-if="video._isConverting" class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-600 dark:border-gray-400 mb-2"></div>
                          <svg v-else class="w-12 h-12 text-gray-400 dark:text-gray-500 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                          </svg>
                          <span class="text-xs text-gray-500 dark:text-gray-400 text-center px-2">
                            {{ video._isConverting 
                              ? (settingStore.language === 'ko' ? '변환 중...' : 'Converting...')
                              : (settingStore.language === 'ko' ? '변환 대기 중...' : 'Waiting for conversion...')
                            }}
                          </span>
                        </div>
                        <!-- 비디오 엘리먼트 표시 (변환된 MP4 또는 지원하는 형식) -->
                        <video v-else-if="video.displayUrl && (!isUnsupportedFormat(video.name || video.title || '') || video.displayUrl?.includes('converted-videos'))"
                          :src="video.displayUrl"
                          class="object-cover rounded-xl transition-opacity duration-300" preload="metadata"
                          :ref="el => (videoRefs[video.id] = el)" @ended="onVideoEnded(video.id)"
                          @timeupdate="updateProgress(video.id, $event)"
                          @loadedmetadata="onVideoMetadataLoaded(video.id, $event)"
                          :class="{ 'brightness-75': !playingVideoIds.includes(video.id) }"></video>
                        <div v-if="video.displayUrl && (!isUnsupportedFormat(video.name || video.title || '') || video.displayUrl?.includes('converted-videos'))"
                          class="absolute inset-0 pointer-events-none transition-colors duration-300"
                          :class="playingVideoIds.includes(video.id) ? 'bg-transparent' : 'bg-black/20'">
                        </div>
                        <span v-else-if="!isUnsupportedFormat(video.name || video.title || '')" class="text-gray-400 dark:text-gray-500">{{ tSummarize.noThumbnail }}</span>
                        <!-- 재생하지 않은 동영상의 영상 길이 표시 (우측 하단) -->
                        <div v-if="video.displayUrl && !playingVideoIds.includes(video.id) && durationMap[video.id]"
                          class="absolute bottom-2 right-2 px-2 py-1 bg-black/70 backdrop-blur-sm text-white text-xs font-medium rounded pointer-events-none">
                          {{ formatTime(durationMap[video.id]) }}
                        </div>
                        <!-- 오버레이 진행바 & 시간 (재생 중일 때만 표시) -->
                        <div v-if="video.displayUrl && playingVideoIds.includes(video.id)"
                          class="absolute bottom-0 left-0 right-0 p-2 bg-black/30 backdrop-blur-sm rounded-b-xl transition-all duration-300 pointer-events-none"
                          :class="{
                            'opacity-100 translate-y-0': hoveredVideoId === video.id,
                            'opacity-0 translate-y-full': hoveredVideoId !== video.id
                          }">
                          <div class="flex flex-col gap-1">
                            <div
                              class="w-full h-2 bg-gray-300/70 rounded-full relative cursor-pointer pointer-events-auto backdrop-blur-sm overflow-visible"
                              @click.stop="seekVideo(video.id, $event)"
                              :ref="el => { if (el) progressBarRefs[video.id] = el }">
                              <div :class="[
                                'h-full bg-gradient-to-r from-emerald-500 to-emerald-600',
                                (isScrubbing && draggingVideoId === video.id)
                                  ? 'transition-none'
                                  : 'transition-[width] duration-150 ease-linear'
                              ]" :style="{ width: `${progress[video.id] || 0}%` }"></div>
                              <div
                                class="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full border border-emerald-500 cursor-pointer shadow hover:shadow-md hover:scale-110 transition-all pointer-events-auto"
                                :style="{ left: `calc(${progress[video.id] || 0}% - 6px)` }"
                                @mousedown="startDragging(video.id, $event)" @click.stop></div>
                            </div>
                            <div
                              class="flex justify-between text-[10px] font-medium text-gray-200 tracking-wide px-1 pointer-events-auto">
                              <span>{{ formatTime(currentTimeMap[video.id] || 0) }}</span>
                              <span>{{ formatTime(durationMap[video.id] || 0) }}</span>
                            </div>
                          </div>
                        </div>
                        <!-- 재생/일시정지 토글 버튼 -->
                        <button @click.stop="togglePlay(video.id)" :class="{
                          'opacity-100 scale-100': hoveredVideoId === video.id || !playingVideoIds.includes(video.id),
                          'opacity-0 scale-90': hoveredVideoId !== video.id && playingVideoIds.includes(video.id)
                        }" class="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-black/60 to-black/40 backdrop-blur-sm text-white rounded-full w-12 h-12 m-auto transition-all duration-300 hover:scale-110 active:scale-95">
                          <svg v-if="!playingVideoIds.includes(video.id)" xmlns="http://www.w3.org/2000/svg"
                            fill="currentColor" viewBox="0.4 -0.7 16 16">
                            <path
                              d="M6.271 4.055a.5.5 0 0 1 .759-.429l4.592 3.11a.5.5 0 0 1 0 .828l-4.592 3.11a.5.5 0 0 1-.759-.429V4.055z" />
                          </svg>
                          <svg v-else xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0.5 0 16 16">
                            <path
                              d="M5.5 3.5A.5.5 0 0 1 6 3h1a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5H6a.5.5 0 0 1-.5-.5v-9zM9.5 3.5A.5.5 0 0 1 10 3h1a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-9z" />
                          </svg>
                        </button>
                      </div>
                      <!-- 동영상 타이틀 및 정보 -->
                      <div class="ml-4 w-full text-left">
                        <div v-if="video.title || video.name" class="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
                          {{ video.title || video.name }}
                        </div>
                        <!-- 영상 정보: 길이, 해상도, 용량 (가로 나열) -->
                        <div class="mt-1 text-xs text-gray-500 dark:text-gray-400 flex flex-wrap items-center gap-x-2 gap-y-0.5">
                          <span v-if="durationMap[video.id]">
                            {{ formatTime(durationMap[video.id]) }}
                          </span>
                          <span v-if="durationMap[video.id] && (video.width && video.height || video.fileSize)" class="text-gray-400">•</span>
                          <span v-if="video.width && video.height">
                            {{ video.width }} × {{ video.height }}
                          </span>
                          <span v-if="video.width && video.height && video.fileSize" class="text-gray-400">•</span>
                          <span v-if="video.fileSize">
                            {{ formatFileSize(video.fileSize) }}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <!-- 확대 뷰 -->
              <div v-else class="flex flex-col items-center w-full">
                <div class="relative w-full h-[100%] mb-2"
                  @mouseenter="videoFiles[zoomedIndex] && (hoveredVideoId = videoFiles[zoomedIndex].id)"
                  @mouseleave="hoveredVideoId = null">
                  <!-- 닫기(X) 버튼 -->
                  <button v-if="videoFiles[zoomedIndex]" @click.stop="unzoomVideo" aria-label="확대 종료" title="닫기"
                    class="absolute top-2 right-2 z-20 w-8 h-8 flex items-center justify-center bg-black/50 hover:bg-black/70 rounded-full text-white shadow transition-all duration-200 hover:scale-110 active:scale-95">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                      class="w-5 h-5">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                  <!-- 지원하지 않는 형식이고 변환 중이거나 변환되지 않은 경우 -->
                  <div v-if="videoFiles[zoomedIndex] && isUnsupportedFormat(videoFiles[zoomedIndex].name || videoFiles[zoomedIndex].title || '') && (videoFiles[zoomedIndex]._isConverting || !videoFiles[zoomedIndex].displayUrl?.includes('converted-videos'))" 
                    class="w-full h-[100%] flex flex-col items-center justify-center bg-gray-200 dark:bg-gray-700 rounded-xl">
                    <div v-if="videoFiles[zoomedIndex]._isConverting" class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-600 dark:border-gray-400 mb-2"></div>
                    <svg v-else class="w-12 h-12 text-gray-400 dark:text-gray-500 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    <span class="text-xs text-gray-500 dark:text-gray-400 text-center px-2">
                      {{ videoFiles[zoomedIndex]._isConverting 
                        ? (settingStore.language === 'ko' ? '변환 중...' : 'Converting...')
                        : (settingStore.language === 'ko' ? '변환 대기 중...' : 'Waiting for conversion...')
                      }}
                    </span>
                  </div>
                  <!-- 비디오 엘리먼트 표시 (변환된 MP4 또는 지원하는 형식) -->
                  <video v-else-if="videoFiles[zoomedIndex] && videoFiles[zoomedIndex].displayUrl && (!isUnsupportedFormat(videoFiles[zoomedIndex].name || videoFiles[zoomedIndex].title || '') || videoFiles[zoomedIndex].displayUrl?.includes('converted-videos'))"
                    :src="videoFiles[zoomedIndex].displayUrl"
                    class="w-full h-[100%] rounded-xl object-cover transition-all duration-300" preload="metadata"
                    :ref="el => { if (el && videoFiles[zoomedIndex]) videoRefs[videoFiles[zoomedIndex].id] = el }"
                    @timeupdate="updateProgress(videoFiles[zoomedIndex].id, $event)"
                    @loadedmetadata="onVideoMetadataLoaded(videoFiles[zoomedIndex].id, $event)"
                    @ended="onVideoEnded(videoFiles[zoomedIndex].id)"
                    :class="{ 'brightness-75': !playingVideoIds.includes(videoFiles[zoomedIndex].id) }"></video>
                  <div v-if="videoFiles[zoomedIndex]"
                    class="absolute inset-0 pointer-events-none transition-colors duration-300"
                    :class="playingVideoIds.includes(videoFiles[zoomedIndex].id) ? 'bg-transparent' : 'bg-black/20'">
                  </div>
                  <!-- 재생하지 않은 동영상의 영상 길이 표시 (우측 하단) -->
                  <div v-if="videoFiles[zoomedIndex] && !playingVideoIds.includes(videoFiles[zoomedIndex].id) && durationMap[videoFiles[zoomedIndex].id]"
                    class="absolute bottom-2 right-2 px-2 py-1 bg-black/70 backdrop-blur-sm text-white text-xs font-medium rounded pointer-events-none">
                    {{ formatTime(durationMap[videoFiles[zoomedIndex].id]) }}
                  </div>
                  <!-- 확대 뷰 재생 진행바 & 시간 (재생 중일 때만 표시) -->
                  <div v-if="videoFiles[zoomedIndex] && playingVideoIds.includes(videoFiles[zoomedIndex].id)"
                    class="absolute bottom-0 left-0 right-0 p-2 bg-black/30 backdrop-blur-sm rounded-b-xl transition-all duration-300 pointer-events-none"
                    :class="{
                      'opacity-100 translate-y-0': hoveredVideoId === videoFiles[zoomedIndex].id,
                      'opacity-0 translate-y-full': hoveredVideoId !== videoFiles[zoomedIndex].id
                    }">
                    <div class="flex flex-col gap-1">
                      <div
                        class="w-full h-2 bg-gray-300/70 rounded-full relative cursor-pointer pointer-events-auto overflow-visible"
                        @click.stop="seekVideo(videoFiles[zoomedIndex].id, $event)"
                        :ref="el => { if (el && videoFiles[zoomedIndex]) progressBarRefs[videoFiles[zoomedIndex].id] = el }">
                        <div :class="[
                          'h-full bg-gradient-to-r from-emerald-500 to-emerald-600',
                          (isScrubbing && draggingVideoId === videoFiles[zoomedIndex].id)
                            ? 'transition-none'
                            : 'transition-[width] duration-150 ease-linear'
                        ]" :style="{ width: `${progress[videoFiles[zoomedIndex].id] || 0}%` }"></div>
                        <div
                          class="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white rounded-full border border-emerald-500 cursor-pointer shadow hover:shadow-md hover:scale-110 transition-all pointer-events-auto"
                          :style="{ left: `calc(${progress[videoFiles[zoomedIndex].id] || 0}% - 8px)` }"
                          @mousedown="startDragging(videoFiles[zoomedIndex].id, $event)" @click.stop></div>
                      </div>
                      <div
                        class="flex justify-between text-[10px] font-medium text-gray-200 tracking-wide px-1 pointer-events-auto">
                        <span>{{ formatTime(currentTimeMap[videoFiles[zoomedIndex].id] || 0) }}</span>
                        <span>{{ formatTime(durationMap[videoFiles[zoomedIndex].id] || 0) }}</span>
                      </div>
                    </div>
                  </div>
                  <!-- 재생/일시정지 토글 버튼 -->
                  <button v-if="videoFiles[zoomedIndex]" @click.stop="togglePlay(videoFiles[zoomedIndex].id)" :class="{
                    'opacity-100 scale-100': hoveredVideoId === videoFiles[zoomedIndex].id || !playingVideoIds.includes(videoFiles[zoomedIndex].id),
                    'opacity-0 scale-90': hoveredVideoId !== videoFiles[zoomedIndex].id && playingVideoIds.includes(videoFiles[zoomedIndex].id)
                  }" class="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-black/60 to-black/40 backdrop-blur-sm text-white rounded-full w-14 h-14 m-auto transition-all duration-300 hover:scale-110 active:scale-95">
                    <svg v-if="!playingVideoIds.includes(videoFiles[zoomedIndex].id)" xmlns="http://www.w3.org/2000/svg"
                      fill="currentColor" viewBox="0.4 -0.7 16 16" class="w-10 h-10">
                      <path
                        d="M6.271 4.055a.5.5 0 0 1 .759-.429l4.592 3.11a.5.5 0 0 1 0 .828l-4.592 3.11a.5.5 0 0 1-.759-.429V4.055z" />
                    </svg>
                    <svg v-else xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0.5 0 16 16"
                      class="w-10 h-10">
                      <path
                        d="M5.5 3.5A.5.5 0 0 1 6 3h1a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5H6a.5.5 0 0 1-.5-.5v-9zM9.5 3.5A.5.5 0 0 1 10 3h1a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-9z" />
                    </svg>
                  </button>
                </div>
                <!-- 하단 되돌아가기 버튼 제거됨: 상단 X 버튼 사용 -->
              </div>
            </template>
          </div>
        </div>

        <!-- 프롬프트 입력 블럭 -->
        <div class="mb-3 flex items-center gap-2">
          <div class="relative flex-1">
            <textarea v-model="prompt"
              class="w-full border border-slate-300 dark:border-gray-600 focus:border-emerald-400 dark:focus:border-emerald-500 focus:ring-2 focus:ring-emerald-300 dark:focus:ring-emerald-500 rounded-xl px-3 py-2 resize-none transition-all bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200"
              :placeholder="tSummarize.promptPlaceholder" rows="3" @keydown.enter.exact.prevent="runInference"></textarea>
            <button
              class="absolute right-[8px] top-[45px] p-2 rounded-lg bg-emerald-500/90 hover:bg-emerald-400 text-white flex items-center justify-center shadow-lg shadow-emerald-500/30 transition-all duration-200 transform hover:scale-[1.03] active:scale-[0.97]"
              @click="runInference" :disabled="videoFiles.length === 0 || selectedIndexes.length === 0">
              <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0.4 -1 16 16" class="w-5 h-5">
                <path
                  d="M6.271 4.055a.5.5 0 0 1 .759-.429l4.592 3.11a.5.5 0 0 1 0 .828l-4.592 3.11a.5.5 0 0 1-.759-.429V4.055z" />
              </svg>
            </button>
          </div>
        </div>

        <input type="file" accept="video/*" multiple @change="onUpload" ref="fileInputRef" class="hidden" />

        <!-- 우클릭 컨텍스트 메뉴 (Teleport로 body에 렌더링) -->
        <Teleport to="body">
          <div v-if="contextMenu.visible" class="fixed z-[200]"
            :style="{ left: `${contextMenu.x}px`, top: `${contextMenu.y}px` }" @click.stop>
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-100 dark:border-gray-700 overflow-hidden w-[200px]">
              <button v-if="selectedIndexes.length < 2" class="w-full text-left px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200"
                @click.stop="contextZoom">{{ tSummarize.expand }}</button>
              <button class="w-full text-left px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200" @click.stop="contextOpenSettings">{{ tSummarize.setting }}</button>
              <div class="h-px bg-gray-100 dark:bg-gray-700"></div>
              <button class="w-full text-left px-4 py-3 text-red-600 dark:text-red-400 hover:bg-gray-50 dark:hover:bg-gray-700" @click.stop="contextDelete">
                {{ selectedIndexes.length > 1 ? `${tSummarize.deleteSelected} (${selectedIndexes.length})` : tSummarize.delete }}
              </button>
            </div>
          </div>
        </Teleport>

        <!-- 경고 모달 -->
        <div v-if="showWarningModal"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-lg w-full p-6">
            <h3 class="text-lg font-semibold mb-2 text-gray-800 dark:text-gray-200">경고</h3>
            <p class="text-sm text-gray-700 dark:text-gray-300 mb-4" v-html="warningMessage"></p>
            <div class="flex justify-end gap-2">
              <button
                class="px-6 py-2.5 rounded-xl bg-emerald-500/90 hover:bg-emerald-400 text-white shadow-lg shadow-emerald-500/30 transition-all duration-200 transform hover:scale-[1.03] active:scale-[0.97]"
                @click="closeWarning">확인</button>
            </div>
          </div>
        </div>

        <div v-if="videoFiles.length === 1" class="mt-2 flex">
          <button @click="removeSingleVideo"
            class="relative flex items-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-br from-red-500 to-red-600 text-white font-medium shadow-lg hover:shadow-xl hover:from-red-600 hover:to-red-700 transition-all duration-300 transform hover:scale-105 active:scale-95">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.9" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 6h18" />
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M8 6V4.8c0-.442 0-.663.074-.842a1 1 0 01.418-.418C8.671 3.466 8.892 3.466 9.334 3.466h5.332c.442 0 .663 0 .842.074a1 1 0 01.418.418c.074.179.074.4.074.842V6m-6 5v5m4-5v5M5 6l1.2 12.4c.109 1.123.163 1.685.44 2.118a2 2 0 00.826.73c.458.222 1.021.222 2.147.222h4.374c1.126 0 1.689 0 2.147-.222a2 2 0 00.826-.73c.277-.433.331-.995.44-2.118L19 6" />
            </svg>
            <span>{{ tSummarize.deleteVideo }}</span>
          </button>
        </div>

        <!-- Setting Modal -->
        <div v-if="showSettingModal"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-[90%] max-h-[90%] w-full p-4 overflow-auto">
            <div class="flex items-center justify-between mb-3 border-b border-slate-800/70 dark:border-gray-200/30 pb-3">
              <div
                class="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 dark:bg-emerald-500/20 border border-emerald-400/40 dark:border-emerald-400/60 w-fit">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                <h3 class="text-[11px] font-semibold tracking-wide text-emerald-600 dark:text-emerald-400 uppercase">Settings</h3>
              </div>
              <button @click="closeSettingModal"
                class="px-2 py-[1px] rounded-full border-[2px] border-slate-500/60 dark:border-gray-600 bg-slate-900/70 dark:bg-gray-700 hover:bg-slate-800/80 dark:hover:bg-gray-600 text-slate-100 dark:text-gray-200 transition-all duration-200">X</button>
            </div>
            <Setting />
          </div>
        </div>

        <!-- 업로드 진행률 모달 -->
        <Teleport to="body">
          <div v-if="showUploadModal" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-2xl w-full mx-4 p-6">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-200">{{ tSummarize.uploading }}</h3>
                <button @click="closeUploadModal" class="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div class="space-y-4 max-h-[60vh] overflow-y-auto">
                <div v-for="(upload, index) in uploadProgress" :key="upload.id" class="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-white dark:bg-gray-700">
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-medium text-gray-700 dark:text-gray-200 truncate flex-1 mr-2">{{ upload.fileName }}</span>
                    <span class="text-sm text-gray-500 dark:text-gray-400 whitespace-nowrap">{{ upload.progress }}%</span>
                  </div>
                  <div class="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2.5 mb-2">
                    <div 
                      class="bg-gradient-to-r from-emerald-500 to-emerald-600 h-2.5 rounded-full transition-all duration-300"
                      :style="{ width: `${upload.progress}%` }"
                    ></div>
                  </div>
                  <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                    <span>{{ upload.status }}</span>
                    <span v-if="upload.uploaded > 0">{{ formatFileSize(upload.uploaded) }} / {{ formatFileSize(upload.total) }}</span>
                  </div>
                </div>
              </div>
              <div v-if="allUploadsComplete" class="mt-4 text-center">
                <button @click="closeUploadModal" class="px-6 py-2 bg-emerald-500 dark:bg-emerald-600 text-white rounded-lg hover:bg-emerald-600 dark:hover:bg-emerald-500 transition-colors">
                  {{ tSummarize.complete }}
                </button>
              </div>
            </div>
          </div>
        </Teleport>
      </section>

      <!-- 우측: 결과/프롬프트 -->
      <section
        class="rounded-2xl p-5 bg-gradient-to-br from-white via-gray-50 to-gray-100 dark:from-gray-950 dark:via-gray-950 dark:to-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm hover:shadow-md transition-shadow duration-300">
        <!-- 헤더 -->
        <header class="flex items-center justify-between px-1 pb-3 mb-3 border-b border-slate-800/70 dark:border-gray-200/30">
          <div class="flex flex-col gap-1">
            <div
              class="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 dark:bg-emerald-500/20 border border-emerald-400/40 dark:border-emerald-400/60 w-fit">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span class="text-[11px] font-semibold tracking-wide text-emerald-600 dark:text-emerald-400 uppercase">
                {{ tSummarize.summaryResult }}
              </span>
            </div>
            <p class="text-xs md:text-sm text-black dark:text-gray-200 mt-1">
              {{ tSummarize.resultDescription }}
            </p>
          </div>
        </header>
        <!-- 채팅 형태 출력 영역 -->
        <div
          class="chat-window border border-gray-200 dark:border-gray-800 rounded-xl bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900 h-[600px] p-3 overflow-auto shadow-inner"
          ref="chatWindowRef">
          <div v-if="chatMessages.length === 0" class="text-gray-400 dark:text-gray-500 text-sm flex items-center justify-center h-full">
            {{ tSummarize.noMessages }}
          </div>
          <template v-else>
            <div v-for="m in chatMessages" :key="m.id" class="chat-row" :class="{
              'from-user': m.role === 'user',
              'from-assistant': m.role === 'assistant',
              'from-system': m.role === 'system'
            }">
              <div class="avatar" :class="{
                'avatar-user': m.role === 'user',
                'avatar-assistant': m.role === 'assistant',
                'avatar-system': m.role === 'system'
              }">
                <span v-if="m.role === 'assistant'">AI</span>
                <span v-else-if="m.role === 'user'">You</span>
                <span v-else>VIX</span>
              </div>
              <div class="chat-bubble" :class="{
                'user': m.role === 'user',
                'assistant': m.role === 'assistant',
                'system': m.role === 'system'
              }">
                <div class="content" v-html="m.content"></div>
                <div class="chat-meta" :class="{ 'justify-end': m.role === 'user' }">
                  <span class="time">{{ new Date(m.time).toLocaleTimeString() }}</span>
                  <button v-if="m.role === 'assistant' || m.role === 'user'" class="copy-btn"
                    @click="copyMessage(m)">복사</button>
                </div>
              </div>
            </div>
          </template>
        </div>

        <div class="flex items-center gap-2 mt-3">
          <input v-model="ask_prompt" :placeholder="tSummarize.askPlaceholder"
            class="w-full rounded-xl border border-slate-300 dark:border-gray-600 focus:border-emerald-500 dark:focus:border-emerald-400 focus:ring-2 focus:ring-emerald-300 dark:focus:ring-emerald-500 px-4 py-3 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 transition-all"
            @keyup.enter="() => { onAsk(ask_prompt); ask_prompt = ''; }" />
          <button
            class="rounded-lg bg-emerald-500/90 hover:bg-emerald-400 text-white px-4 py-2 shadow-lg shadow-emerald-500/30 transition-all duration-200 transform hover:scale-[1.03] active:scale-[0.97]"
            @click="() => { onAsk(ask_prompt); ask_prompt = ''; }">
            {{ tSummarize.ask }}
          </button>
        </div>

        <div class="mt-3 flex gap-2">
          <button
            class="px-3 py-2 rounded-md border border-slate-500/60 dark:border-gray-600 text-[13px] text-slate-100 dark:text-gray-200 bg-slate-900/70 dark:bg-gray-800 hover:bg-slate-800/80 dark:hover:bg-gray-700 hover:border-emerald-400/70 dark:hover:border-emerald-500 hover:text-emerald-50 dark:hover:text-emerald-300 shadow-sm transition-all duration-200"
            @click="saveResult">{{ tSummarize.saveResult }}</button>
          <button
            class="px-3 py-2 rounded-md border border-slate-500/60 dark:border-gray-600 text-[13px] text-slate-100 dark:text-gray-200 bg-slate-900/70 dark:bg-gray-800 hover:bg-slate-800/80 dark:hover:bg-gray-700 hover:border-emerald-400/70 dark:hover:border-emerald-500 hover:text-emerald-50 dark:hover:text-emerald-300 shadow-sm transition-all duration-200"
            @click="clear">{{ tSummarize.clear }}</button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, onActivated, computed, nextTick, watch } from "vue";
import { useSummaryVideoStore } from '@/stores/summaryVideoStore';
import { useSettingStore } from '@/stores/settingStore';
import { marked } from 'marked';
import Setting from '@/components/Setting.vue';
import settingIcon from '@/assets/icons/setting.png';

// ==================== 상수 정의 ====================
const API_BASE_URL = 'http://172.16.15.69:8001';

// VIA 파일 목록 조회 함수
async function loadViaFiles() {
  try {
    const response = await fetch(`${API_BASE_URL}/via-files?purpose=vision`);
    if (!response.ok) {
      console.warn('VIA 파일 목록 조회 실패:', response.status);
      return null;
    }
    const data = await response.json();
    if (data && data.data) {
      console.log('VIA 서버 파일 목록:', data.data);
      return data.data;
    }
    return null;
  } catch (error) {
    console.error('VIA 파일 목록 조회 중 오류:', error);
    return null;
  }
}

// 지원하지 않는 형식 목록
const UNSUPPORTED_VIDEO_FORMATS = ['avi', 'mkv', 'flv', 'wmv']; // 브라우저가 직접 재생하지 못하는 형식

// 동영상 파일 확장자 추출 함수
function getVideoFileExtension(filename) {
  return filename.toLowerCase().split('.').pop();
}

// 지원하지 않는 형식인지 확인하는 함수
function isUnsupportedFormat(filename) {
  return UNSUPPORTED_VIDEO_FORMATS.includes(getVideoFileExtension(filename));
}

// 동영상을 MP4로 변환하는 함수
async function convertVideoToMp4(videoId, userId, videoObject) {
  // 변환 중 상태 표시
  if (videoObject) {
    videoObject._isConverting = true;
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}/convert-video/${videoId}?user_id=${userId}`);
    if (!response.ok) {
      console.warn('동영상 변환 요청 실패:', response.status);
      if (videoObject) {
        videoObject._isConverting = false;
      }
      return null;
    }
    const data = await response.json();
    if (data.success && data.converted_url) {
      // 변환된 MP4 URL을 displayUrl로 업데이트
      videoObject.displayUrl = data.converted_url;
      videoObject.originUrl = data.converted_url;
      videoObject._isConverting = false;
      console.log('동영상 변환 완료:', {
        title: videoObject.name || videoObject.title,
        convertedUrl: data.converted_url
      });
      return data.converted_url;
    }
    if (videoObject) {
      videoObject._isConverting = false;
    }
    return null;
  } catch (error) {
    console.error('동영상 변환 중 오류:', error);
    if (videoObject) {
      videoObject._isConverting = false;
    }
    return null;
  }
}

const METADATA_TIMEOUT = 5000; // 동영상 메타데이터 로드 타임아웃 (ms)
const CHUNK_SIZE_UPDATE_DELAY = 1000; // chunk_size 업데이트 지연 시간 (ms)
const UPLOAD_PROCESSING_DELAY = 500; // 업로드 후 처리 지연 시간 (ms)
const AUTO_SAVE_DELAY = 1000; // 자동 저장 지연 시간 (ms)

// ==================== 다국어 지원 ====================
const summarizeTranslations = {
  ko: {
    workspace: "Video Summarize Workspace",
    videoSection: "Video Section",
    adjustPerformance: "요약 성능을 조정하고 싶다면 우측의 설정 버튼을 클릭하여 조정할 수 있습니다.",
    setting: "설정",
    dropVideo: "Drop Video here",
    or: "-- or --",
    clickUpload: "Click to upload",
    dropHere: "여기에 파일을 놓으세요",
    noThumbnail: "No Thumbnail",
    expand: "확대",
    delete: "삭제",
    deleteSelected: "선택된 항목 삭제",
    deleteVideo: "동영상 삭제",
    promptPlaceholder: "프롬프트를 입력하세요.",
    summaryResult: "Summary Result",
    resultDescription: "요약 결과를 확인하고 질문을 입력할 수 있습니다.",
    noMessages: "아직 메시지가 없습니다. 요약을 실행하거나 질문을 입력하세요.",
    askPlaceholder: "질문을 입력하세요...",
    ask: "Ask",
    saveResult: "결과 저장",
    clear: "초기화",
    uploading: "동영상 업로드 중...",
    complete: "완료"
  },
  en: {
    workspace: "Video Summarize Workspace",
    videoSection: "Video Section",
    adjustPerformance: "Click the settings button on the right to adjust summarization performance.",
    setting: "Settings",
    dropVideo: "Drop Video here",
    or: "-- or --",
    clickUpload: "Click to upload",
    dropHere: "Drop files here",
    noThumbnail: "No Thumbnail",
    expand: "Expand",
    delete: "Delete",
    deleteSelected: "Delete Selected",
    deleteVideo: "Delete Video",
    promptPlaceholder: "Enter a prompt...",
    summaryResult: "Summary Result",
    resultDescription: "View summary results and enter questions.",
    noMessages: "No messages yet. Run a summary or enter a question.",
    askPlaceholder: "Enter a question...",
    ask: "Ask",
    saveResult: "Save Result",
    clear: "Clear",
    uploading: "Uploading videos...",
    complete: "Complete"
  }
};

const tSummarize = computed(() => summarizeTranslations[settingStore.language] || summarizeTranslations.ko);

const selectedIndexes = ref([]); // 선택된 동영상 id 배열
const prompt = ref("");
const response = ref("");
// 마지막으로 요약된 비디오의 서버 video_id (다른 함수에서 재사용 가능)
const summarizedVideoId = ref(null); // 마지막으로 요약된 서버 video_id
const summarizedVideoMap = ref({}); // 로컬 video.id -> 서버 video_id 매핑 (다중 요약 지원)
// 채팅 메시지 배열: { id, role: 'user' | 'assistant' | 'system', content(html) }
const chatMessages = ref([]);
const chatWindowRef = ref(null); // 채팅 자동 스크롤용
const isDragging = ref(false); // 업로드 영역 드래그 상태
const isScrubbing = ref(false); // 재생바(진행 막대) 드래그 상태
const fileInputRef = ref(null);
const ask_prompt = ref("");
// 확대 기능 상태
const isZoomed = ref(false); // 확대 여부 (멀티 비디오 전용)
const zoomedIndex = ref(null); // 확대된 비디오 인덱스
const settingStore = useSettingStore();
const videoFiles = ref([]); // Summarize 메뉴의 로컬 동영상 배열
// videoUrls 제거: 템플릿에서 사용되지 않아 메모리 관리 단순화
const summaryVideoStore = useSummaryVideoStore();
// 샘플 동영상 경로 (서버에서 제공하는 정적 파일 경로 사용)
const sampleVideoPath = ref(null); // 동적으로 설정
const sampleVideoRef = ref(null); // 샘플 동영상 ref
// 재생 버튼 상태 (Video Storage 스타일 이식)
const hoveredVideoId = ref(null); // Track the hovered video ID
const playingVideoIds = ref([]); // 재생 중인 비디오 id 목록
const videoRefs = ref({}); // id -> video 요소
// 단일 영상 안전 접근용 computed (삭제/비움 시 에러 방지)
const singleVideo = computed(() => (videoFiles.value.length === 1 ? videoFiles.value[0] : null));
const progress = ref({});
const currentTimeMap = ref({}); // 비디오별 현재 재생 시간(초)
const durationMap = ref({});    // 비디오별 전체 길이(초)
const dragVideoId = ref(null); // 업로드 영역용 id
const draggingVideoId = ref(null); // 재생바 스크러빙 중인 비디오 id
const progressBarRefs = ref({}); // 비디오별 진행바 엘리먼트 참조
let draggingBarEl = null; // 현재 드래그 중인 진행바 엘리먼트
// 설정 모달 상태
const showSettingModal = ref(false);
// 우클릭 컨텍스트 메뉴 상태
const contextMenu = ref({ visible: false, x: 0, y: 0, video: null, index: null });
// 스트리밍 상태 (동영상 업로드 여부)
const streaming = ref(false);
// 업로드 진행률 모달 상태
const showUploadModal = ref(false);
const uploadProgress = ref([]); // { id, fileName, progress, status, uploaded, total }
const activeUploads = ref({}); // { uploadId: XMLHttpRequest } - 진행 중인 업로드 추적
// 실행 중인 작업 추적
const activeTasks = ref([]); // 실행 중인 작업 목록: { taskId, type, startTime, currentIndex, totalCount, videoIds, loadingIds, prompt }
const activeIntervals = ref({}); // 실행 중인 타이머: { taskId: intervalId }

// 전역 작업 관리자 초기화 (페이지 전환 후에도 작업이 계속 진행되도록)
if (!window.__vssActiveTasks) {
  window.__vssActiveTasks = new Map();
}
if (!window.__vssTaskResults) {
  window.__vssTaskResults = new Map(); // 작업 완료 결과 저장
}

function closeSettingModal() { showSettingModal.value = false; }

// ==================== 유틸리티 함수 ====================
/**
 * 동영상 길이를 가져와서 추천 chunk_size를 계산하는 함수
 */
async function RecommendChunkSize(videoElement) {
  if (!videoElement) return null;

  return new Promise((resolve) => {
    if (videoElement.duration && isFinite(videoElement.duration)) {
      resolve(videoElement.duration);
      return;
    }

    const onLoadedMetadata = () => {
      if (videoElement.duration && isFinite(videoElement.duration)) {
        videoElement.removeEventListener('loadedmetadata', onLoadedMetadata);
        resolve(videoElement.duration);
      }
    };

    videoElement.addEventListener('loadedmetadata', onLoadedMetadata);

    // 타임아웃 설정
    setTimeout(() => {
      videoElement.removeEventListener('loadedmetadata', onLoadedMetadata);
      resolve(null);
    }, METADATA_TIMEOUT);
  });
}

/**
 * 추천 chunk_size를 API에서 가져오는 함수
 */
async function fetchRecommendedChunkSize(videoLength) {
  if (!videoLength || !isFinite(videoLength)) return null;

  try {
    const response = await fetch(`${API_BASE_URL}/get-recommended-chunk-size`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ video_length: videoLength })
    });

    if (!response.ok) {
      console.warn('추천 chunk_size 가져오기 실패:', response.status);
      return null;
    }

    const data = await response.json();
    return data.recommended_chunk_size;
  } catch (error) {
    console.warn('추천 chunk_size 가져오기 중 오류:', error);
    return null;
  }
}

/**
 * 동영상에 대해 추천 chunk_size를 가져와서 설정 스토어에 저장
 */
async function updateRecommendedChunkSize(videoId) {
  const videoElement = videoRefs.value[videoId];
  if (!videoElement) return;

  const duration = await RecommendChunkSize(videoElement);
  if (!duration) {
    console.warn(`동영상 ${videoId}의 길이를 가져올 수 없습니다.`);
    return;
  }

  const recommendedChunkSize = await fetchRecommendedChunkSize(duration);
  if (recommendedChunkSize !== null && settingStore) {
    // 추천된 chunk_size를 설정 스토어에 저장
    settingStore.chunk = recommendedChunkSize;
  }
}

/**
 * 비디오 객체 생성 헬퍼 함수
 */
function createVideoObject(videoData, file = null) {
  const hasFile = file instanceof File;
  const summaryObjectUrl = hasFile ? URL.createObjectURL(file) : null;
  const displayUrl = summaryObjectUrl || videoData.displayUrl || videoData.originUrl || videoData.url || '';
  const originUrl = videoData.originUrl || videoData.url || displayUrl;

  return {
    id: videoData.id || videoData.video_id,
    name: videoData.name || videoData.title,
    originUrl,
    displayUrl,
    summaryObjectUrl,
    date: videoData.date || new Date().toISOString().slice(0, 10),
    summary: videoData.summary || '',
    file: hasFile ? file : null,
    dbId: videoData.dbId || videoData.id || videoData.video_id,
    _isConverting: false // 변환 중 상태 추적
  };
}

/**
 * 파일 필터링 헬퍼 함수
 */
function filterVideoFiles(files) {
  return Array.from(files).filter((file) => {
    if (!file.type.startsWith('video/')) {
      alert('동영상 파일만 업로드할 수 있습니다.');
      return false;
    }
    return true;
  });
}

/**
 * 중복 파일명 체크 헬퍼 함수
 */
async function checkDuplicateFiles(files, userId) {
  try {
    const response = await fetch(`${API_BASE_URL}/videos?user_id=${userId}`);
    if (response.ok) {
      const data = await response.json();
      if (data.success && data.videos) {
        const existingFileNames = new Set(data.videos.map(v => v.title));
        const duplicateFiles = files.filter(file => existingFileNames.has(file.name));
        
        if (duplicateFiles.length > 0) {
          const duplicateNames = duplicateFiles.map(f => f.name).join(', ');
          alert(`이미 업로드된 동영상입니다: ${duplicateNames}`);
          return true; // 중복 파일 있음
        }
      }
    }
  } catch (error) {
    // 중복 체크 실패 시 업로드 계속 진행
  }
  return false; // 중복 파일 없음
}

function scrollChatToBottom() {
  nextTick(() => {
    if (chatWindowRef.value) {
      chatWindowRef.value.scrollTop = chatWindowRef.value.scrollHeight;
    }
  });
}

function addChatMessage(message) {
  const enriched = {
    id: message.id || Date.now() + Math.random(),
    role: message.role || 'system',
    content: message.content || '',
    time: message.time || new Date().toISOString()
  };
  chatMessages.value.push(enriched);
  scrollChatToBottom();
}

function updateProgress(videoId, event) {
  if (!videoId) return;
  const video = videoRefs.value && videoRefs.value[videoId];
  if (!video) return;
  if (typeof video.duration !== 'number' || !Number.isFinite(video.duration) || video.duration === 0) return;
  progress.value[videoId] = (video.currentTime / video.duration) * 100;
  currentTimeMap.value[videoId] = video.currentTime;
  durationMap.value[videoId] = video.duration;
}

function onVideoMetadataLoaded(videoId, event) {
  const video = videoFiles.value.find(v => v.id === videoId);
  if (video && event.target) {
    const { videoWidth, videoHeight, duration } = event.target;
    if (videoWidth && videoHeight) {
      video.width = videoWidth;
      video.height = videoHeight;
    }
    if (duration && isFinite(duration)) {
      durationMap.value[videoId] = duration;
    }
  }
}

function seekVideo(videoId, event) {
  const videoElement = videoRefs.value[videoId];
  if (!videoElement) return;

  const { left, width } = event.currentTarget.getBoundingClientRect();
  videoElement.currentTime = ((event.clientX - left) / width) * videoElement.duration;
}

function startDragging(videoId, evt) {
  // 재생바 스크러빙 시작
  isScrubbing.value = true;
  draggingVideoId.value = videoId;
  // 진행바 엘리먼트 확보 (ref 사용, 없으면 이벤트 타겟에서 추론)
  draggingBarEl = progressBarRefs.value[videoId] || (evt.target && evt.target.closest('.relative.cursor-pointer'));
  document.addEventListener('mousemove', handleScrubMove);
  document.addEventListener('mouseup', stopScrubbing);
  evt.preventDefault();
}

function handleScrubMove(event) {
  if (!isScrubbing.value || !draggingVideoId.value || !draggingBarEl) return;
  const videoElement = videoRefs.value[draggingVideoId.value];
  if (!videoElement || !videoElement.duration) return;
  const { left, width } = draggingBarEl.getBoundingClientRect();
  const ratio = (event.clientX - left) / width;
  const clamped = Math.max(0, Math.min(ratio, 1));
  videoElement.currentTime = clamped * videoElement.duration;
  // 수동 진행도 업데이트 (재생 중이 아닐 때 즉시 반영)
  progress.value[draggingVideoId.value] = clamped * 100;
}

function stopScrubbing() {
  isScrubbing.value = false;
  draggingVideoId.value = null;
  draggingBarEl = null;
  document.removeEventListener('mousemove', handleScrubMove);
  document.removeEventListener('mouseup', stopScrubbing);
}

// 누락된 File 객체를 복원하기 위한 비동기 헬퍼 (object/display URL로 Blob 재생성)
async function restoreMissingFile(video) {
  if (!video || video.file instanceof File) return;
  const src = video.displayUrl || video.originUrl;
  if (!src) return;
  try {
    const resp = await fetch(src);
    const blob = await resp.blob();
    // 파일명 추론: name/title/기본값
    const filename = (video.name || video.title || 'video') + (blob.type && !blob.type.includes('mp4') ? '' : '.mp4');
    video.file = new File([blob], filename, { type: blob.type || 'video/mp4' });
  } catch (e) {
    // File 복원 실패 시 무시
  }
}

async function restoreAllMissingFiles() {
  const targets = videoFiles.value.filter(v => !(v.file instanceof File) && (v.displayUrl || v.originUrl));
  for (const v of targets) {
    await restoreMissingFile(v);
  }
}

/**
 * 현재 사용자의 동영상 ID 목록을 DB에서 가져오는 함수
 */
async function getCurrentUserVideoIds() {
  const userId = localStorage.getItem("vss_user_id");
  if (!userId) return new Set();

  try {
    const response = await fetch(`${API_BASE_URL}/videos?user_id=${userId}`);
    if (!response.ok) {
      console.warn('동영상 목록 조회 실패');
      return new Set();
    }
    const data = await response.json();
    if (data.success && data.videos) {
      // DB ID 목록 반환
      return new Set(data.videos.map(v => v.id));
    }
  } catch (error) {
    console.warn('동영상 목록 조회 중 오류:', error);
  }
  return new Set();
}

// 동영상 목록에서 현재 사용자의 동영상만 필터링하는 함수
async function filterVideosByCurrentUser(videos) {
  if (!videos || videos.length === 0) return [];
  
  const userId = localStorage.getItem("vss_user_id");
  if (!userId) {
    // 사용자 ID가 없으면 모든 동영상 제거
    return [];
  }

  // DB에서 현재 사용자의 동영상 ID 목록 가져오기
  const userVideoIds = await getCurrentUserVideoIds();
  if (userVideoIds.size === 0) {
    // 사용자의 동영상이 없으면 모든 동영상 제거
    return [];
  }

  // 현재 사용자의 동영상만 필터링 (dbId 또는 id로 비교)
  return videos.filter(v => {
    const videoId = v.dbId || v.id;
    return videoId && userVideoIds.has(videoId);
  });
}

// summaryVideoStore에서 동영상을 로드하여 videoFiles에 설정하는 함수
async function loadVideosFromStore() {
  const userId = localStorage.getItem("vss_user_id");
  if (!userId) {
    return false;
    }

    if (Array.isArray(summaryVideoStore.videos) && summaryVideoStore.videos.length > 0) {
      // 현재 사용자의 동영상만 필터링
      const filteredVideos = await filterVideosByCurrentUser(summaryVideoStore.videos);
      
      if (filteredVideos.length > 0) {
      // 기존 summaryObjectUrl 정리 (메모리 누수 방지)
      videoFiles.value.forEach(v => {
        if (v.summaryObjectUrl) {
          try {
            URL.revokeObjectURL(v.summaryObjectUrl);
          } catch (_) {}
        }
      });

        // 동영상이 변경되면 기존 요약 메시지 정리 (중복 방지)
        const newVideoIds = new Set(filteredVideos.map(v => v.id || v.dbId));
        const currentVideoIds = new Set(videoFiles.value.map(v => v.id));
        const videosChanged = newVideoIds.size !== currentVideoIds.size || 
                             Array.from(newVideoIds).some(id => !currentVideoIds.has(id));
        
        if (videosChanged) {
          // 동영상이 변경되었으면 기존 요약 메시지 제거
          chatMessages.value = chatMessages.value.filter(m => {
            // 시스템 메시지나 사용자 메시지는 유지, 요약 결과만 제거
            if (m.role === 'assistant' && m.content.includes('요약')) {
              return false;
            }
            return true;
          });
        }

        // Summarize 전용 표시 URL을 분리하여 Video Storage 원본 URL(ObjectURL)과 독립
        videoFiles.value = await Promise.all(filteredVideos.map(async v => {
          const hasFile = v.file instanceof File;
          // File 객체가 있으면 새로운 ObjectURL 생성, 없으면 기존 displayUrl 또는 originUrl 사용
          const summaryObjectUrl = hasFile ? URL.createObjectURL(v.file) : null;
          // displayUrl 우선순위: summaryObjectUrl > v.displayUrl > v.originUrl > v.url
          const displayUrl = summaryObjectUrl || v.displayUrl || v.originUrl || v.url || '';
          const originUrl = v.originUrl || v.url || displayUrl;
          
          const videoObj = {
            id: v.id,
            name: v.name ?? v.title,
            originUrl, // Video Storage에서 넘어온 원본 URL (삭제 시 revoke 금지)
            displayUrl, // 렌더링에 사용할 URL
            summaryObjectUrl, // Summarize가 관리/해제할 URL (없으면 null)
            date: v.date ?? '',
            summary: v.summary ?? '',
            file: hasFile ? v.file : null,
            dbId: v.dbId || v.id, // DB ID 저장
            _isConverting: false // 변환 중 상태 추적
          };
          
          // 지원하지 않는 형식인 경우 MP4로 변환 요청
          if (isUnsupportedFormat(v.name || v.title || '')) {
            await convertVideoToMp4(videoObj.dbId, userId, videoObj);
          }
          
          return videoObj;
        }));
        selectedIndexes.value = videoFiles.value.map(v => v.id);
        zoomedIndex.value = videoFiles.value.length > 0 ? 0 : null;
        // 동영상이 있으면 streaming을 true로 설정
        streaming.value = videoFiles.value.length > 0;
        // 초기 로딩 후 File 객체가 null인 항목 복원 시도 (세션 재진입, localStorage 경유 케스)
        restoreAllMissingFiles();

        // Video Storage에서 넘어온 동영상들에 대해 추천 chunk_size 계산
        nextTick(() => {
          setTimeout(() => {
            videoFiles.value.forEach(video => {
              updateRecommendedChunkSize(video.id);
            });
        }, CHUNK_SIZE_UPDATE_DELAY);
        });
        
        // DB에서 저장된 요약 결과 로드
        await loadSummariesFromDB();
        
        // VIA 서버 파일 목록 조회 (동기화 확인용)
        await loadViaFiles();
        
        // 채팅 스크롤 처리
        nextTick(() => {
          scrollChatToBottom();
        });
      return true;
      } else {
        // 현재 사용자의 동영상이 없으면 summaryVideoStore도 정리
        summaryVideoStore.clearVideos();
      return false;
      }
    }
  return false;
}

// Pinia 스토어에서 동영상 목록을 불러와서 Summarize 메뉴의 로컬 배열에 복사
onMounted(async () => {
  document.addEventListener('click', handleGlobalClick);
  // 다른 메뉴가 열렸을 때 컨텍스트 메뉴 닫기
  window.addEventListener('profile-menu-opened', closeContextMenu);

  const userId = localStorage.getItem("vss_user_id");
  if (!userId) {
    // 사용자 ID가 없으면 모든 상태 초기화
    videoFiles.value = [];
    summaryVideoStore.clearVideos();
    const storageKey = getStorageKey();
    localStorage.removeItem(storageKey);
    return;
  }

  // 먼저 localStorage에서 상태 복원 시도
  const restored = restoreStateFromLocalStorage();

  // 샘플 동영상 경로 초기화
  sampleVideoPath.value = `${API_BASE_URL}/sample/sample.mp4`;

  // 상태가 복원되지 않았거나 동영상이 없는 경우에만 기본 초기화
  if (!restored || videoFiles.value.length === 0) {
    // 초기 상태: 동영상이 없으면 streaming을 false로 설정
    streaming.value = false;

    // 샘플 동영상 재생 시작 (동영상이 없을 때만)
    if (sampleVideoPath.value && sampleVideoRef.value && !streaming.value) {
      nextTick(() => {
        const video = sampleVideoRef.value;
        if (video) {
          video.play().catch(() => {});
        }
      });
    }

    // summaryVideoStore에서 동영상 로드
    await loadVideosFromStore();
  } else {
    // 상태가 복원된 경우
    // summaryVideoStore에 새로운 동영상이 있으면 우선시 (Search.vue에서 새로 선택한 경우)
    if (Array.isArray(summaryVideoStore.videos) && summaryVideoStore.videos.length > 0) {
      const storeVideoIds = new Set(summaryVideoStore.videos.map(v => v.id || v.dbId));
      const currentVideoIds = new Set(videoFiles.value.map(v => v.id));
      
      // 동영상 목록이 다르면 summaryVideoStore의 동영상으로 업데이트
      const isDifferent = storeVideoIds.size !== currentVideoIds.size || 
                          Array.from(storeVideoIds).some(id => !currentVideoIds.has(id));
      
      if (isDifferent) {
        await loadVideosFromStore();
      } else {
        // 동영상이 같으면 복원된 상태 유지하되, 현재 사용자의 것인지 확인
        if (videoFiles.value.length > 0) {
          const filteredVideos = await filterVideosByCurrentUser(videoFiles.value);
          if (filteredVideos.length !== videoFiles.value.length) {
            // 일부 동영상이 현재 사용자의 것이 아니면 필터링된 목록으로 교체
            videoFiles.value = filteredVideos;
            if (videoFiles.value.length === 0) {
              // 모든 동영상이 제거되었으면 상태 초기화
              streaming.value = false;
              selectedIndexes.value = [];
              isZoomed.value = false;
              zoomedIndex.value = null;
              prompt.value = "";
              response.value = "";
              chatMessages.value = [];
            }
          }
        }
        
        // DB에서 저장된 요약 결과 로드
        await loadSummariesFromDB();
        
        // 채팅 스크롤 처리
        nextTick(() => {
          scrollChatToBottom();
        });
      }
    } else {
      // summaryVideoStore가 비어있으면 복원된 상태 유지
      if (videoFiles.value.length > 0) {
        const filteredVideos = await filterVideosByCurrentUser(videoFiles.value);
        if (filteredVideos.length !== videoFiles.value.length) {
          // 일부 동영상이 현재 사용자의 것이 아니면 필터링된 목록으로 교체
          videoFiles.value = filteredVideos;
          if (videoFiles.value.length === 0) {
            // 모든 동영상이 제거되었으면 상태 초기화
            streaming.value = false;
            selectedIndexes.value = [];
            isZoomed.value = false;
            zoomedIndex.value = null;
            prompt.value = "";
            response.value = "";
            chatMessages.value = [];
          }
        }
      }
      
      // DB에서 저장된 요약 결과 로드
      await loadSummariesFromDB();
      
      // 채팅 스크롤 처리
      nextTick(() => {
        scrollChatToBottom();
      });
    }
  }
});

// summaryVideoStore.videos 변경 감지하여 자동 업데이트
watch(() => summaryVideoStore.videos, async (newVideos, oldVideos) => {
  const userId = localStorage.getItem("vss_user_id");
  if (!userId) {
    return;
  }

  // 새로운 동영상이 있고, 실제로 변경되었는지 확인
  if (Array.isArray(newVideos) && newVideos.length > 0) {
    // 현재 videoFiles와 비교하여 변경되었는지 확인
    const storeVideoIds = new Set(newVideos.map(v => v.id || v.dbId));
    const currentVideoIds = new Set(videoFiles.value.map(v => v.id));
    
    // 동영상 목록이 다르면 업데이트
    const isDifferent = storeVideoIds.size !== currentVideoIds.size || 
                        Array.from(storeVideoIds).some(id => !currentVideoIds.has(id));
    
    if (isDifferent) {
      // summaryVideoStore에서 동영상 로드
      await loadVideosFromStore();
    }
  } else if (newVideos.length === 0 && videoFiles.value.length > 0) {
    // summaryVideoStore가 비어있는데 videoFiles에 동영상이 있으면 초기화
    videoFiles.value.forEach(v => {
      if (v.summaryObjectUrl) {
        try {
          URL.revokeObjectURL(v.summaryObjectUrl);
        } catch (_) {}
      }
    });
    videoFiles.value = [];
    selectedIndexes.value = [];
    isZoomed.value = false;
    zoomedIndex.value = null;
    streaming.value = false;
  }
}, { deep: true });

// 컴포넌트가 활성화될 때마다 실행 (Search.vue에서 다른 동영상 선택 후 돌아올 때)
onActivated(async () => {
  const userId = localStorage.getItem("vss_user_id");
  if (!userId) {
    return;
  }

  // 진행 중인 작업의 결과 확인 및 UI 업데이트
  await checkAndUpdateTaskResults();

  // summaryVideoStore에 새로운 동영상이 있는지 확인
  if (Array.isArray(summaryVideoStore.videos) && summaryVideoStore.videos.length > 0) {
    // 현재 videoFiles와 비교하여 변경되었는지 확인
    const storeVideoIds = new Set(summaryVideoStore.videos.map(v => v.id || v.dbId));
    const currentVideoIds = new Set(videoFiles.value.map(v => v.id));
    
    // 동영상 목록이 다르면 업데이트
    const isDifferent = storeVideoIds.size !== currentVideoIds.size || 
                        Array.from(storeVideoIds).some(id => !currentVideoIds.has(id));
    
    if (isDifferent) {
      // summaryVideoStore에서 동영상 로드
      await loadVideosFromStore();
    }
  } else if (videoFiles.value.length > 0) {
    // summaryVideoStore가 비어있는데 videoFiles에 동영상이 있으면 초기화
    // (다른 페이지에서 동영상을 삭제한 경우)
    videoFiles.value.forEach(v => {
      if (v.summaryObjectUrl) {
        try {
          URL.revokeObjectURL(v.summaryObjectUrl);
        } catch (_) {}
      }
    });
    videoFiles.value = [];
    selectedIndexes.value = [];
    isZoomed.value = false;
    zoomedIndex.value = null;
    streaming.value = false;
  }
});

/**
 * 진행 중인 작업의 결과를 확인하고 UI에 업데이트
 */
async function checkAndUpdateTaskResults() {
  const userId = localStorage.getItem("vss_user_id");
  if (!userId) return;

  // 전역 작업 관리자에서 진행 중인 작업 확인
  for (const [taskId, taskInfo] of window.__vssActiveTasks.entries()) {
    // 작업이 완료되었는지 확인
    if (taskInfo.status === 'completed') {
      // 완료된 작업의 결과를 UI에 반영
      await applyTaskResults(taskId, taskInfo);
      continue;
    }

    // localStorage에서 작업 상태 확인
    const storageKey = `vss_active_task_${userId}_${taskId}`;
    const savedTaskState = localStorage.getItem(storageKey);
    if (savedTaskState) {
      try {
        const taskState = JSON.parse(savedTaskState);
        // 작업이 완료되었는지 확인
        if (taskState.completedVideos && taskState.completedVideos.length > 0) {
          // 완료된 비디오의 결과를 UI에 반영
          for (const completedVideo of taskState.completedVideos) {
            const resultKey = `vss_task_result_${taskId}_${completedVideo.videoId}`;
            const result = window.__vssTaskResults.get(resultKey);
            if (result && !chatMessages.value.some(m => 
              m.role === 'assistant' && m.content.includes(`'${completedVideo.videoName}'`) && m.content.includes('요약 완료')
            )) {
              // 결과를 UI에 추가
              addChatMessage({
                id: Date.now() + Math.random(),
                role: 'assistant',
                content: result.summaryHtml
              });
              
              // 요약 결과를 동영상 객체에 저장
              const video = videoFiles.value.find(v => v.id === completedVideo.videoId);
              if (video) {
                video.summary = completedVideo.summaryText;
                summarizedVideoMap.value[video.id] = completedVideo.serverVideoId;
              }
            }
          }
        }
      } catch (e) {
        console.warn('작업 상태 파싱 실패:', e);
      }
    }
  }

  // 전역 작업 결과에서 새로운 결과 확인
  for (const [resultKey, result] of window.__vssTaskResults.entries()) {
    if (result.timestamp && Date.now() - result.timestamp < 60000) { // 1분 이내 결과만
      // 이미 표시된 결과인지 확인
      const alreadyShown = chatMessages.value.some(m => 
        m.role === 'assistant' && m.content.includes(`'${result.videoName}'`) && m.content.includes('요약 완료')
      );
      
      if (!alreadyShown) {
        // 결과를 UI에 추가
        addChatMessage({
          id: Date.now() + Math.random(),
          role: 'assistant',
          content: result.summaryHtml
        });
        
        // 요약 결과를 동영상 객체에 저장
        const video = videoFiles.value.find(v => v.id === result.videoId);
        if (video) {
          video.summary = result.summaryText;
          summarizedVideoMap.value[video.id] = result.serverVideoId;
        }
      }
    }
  }
}

/**
 * 작업 완료 결과를 UI에 적용
 */
async function applyTaskResults(taskId, taskInfo) {
  // 완료된 비디오의 결과를 UI에 반영
  for (const completedVideo of taskInfo.completedVideos) {
    const resultKey = `vss_task_result_${taskId}_${completedVideo.videoId}`;
    const result = window.__vssTaskResults.get(resultKey);
    if (result && !chatMessages.value.some(m => 
      m.role === 'assistant' && m.content.includes(`'${completedVideo.videoName}'`) && m.content.includes('요약 완료')
    )) {
      addChatMessage({
        id: Date.now() + Math.random(),
        role: 'assistant',
        content: result.summaryHtml
      });
      
      // 요약 결과를 동영상 객체에 저장
      const video = videoFiles.value.find(v => v.id === completedVideo.videoId);
      if (video) {
        video.summary = completedVideo.summaryText;
        summarizedVideoMap.value[video.id] = completedVideo.serverVideoId;
      }
    }
  }

  // 전체 완료 메시지 추가
  if (taskInfo.completedVideos.length > 0) {
    const alreadyShown = chatMessages.value.some(m => 
      m.role === 'system' && m.content.includes('모든 요약 처리 완료')
    );
    
    if (!alreadyShown) {
      addChatMessage({
        id: Date.now() + Math.random(),
        role: 'system',
        content: `✅ 모든 요약 처리 완료 (${taskInfo.completedVideos.length}개 성공). 질의 시 선택된 영상의 서버 요약을 우선 사용합니다.`
      });
    }
  }
}

// 작업 완료 이벤트 리스너 등록
window.addEventListener('vss-task-completed', async (event) => {
  const { taskId, taskInfo } = event.detail;
  await applyTaskResults(taskId, taskInfo);
});

// DB에서 저장된 요약 결과를 로드하는 함수
async function loadSummariesFromDB() {
  const userId = localStorage.getItem("vss_user_id");
  if (!userId || videoFiles.value.length === 0) {
    return;
  }
  
  try {
    // 각 동영상의 요약 결과를 조회
    for (const video of videoFiles.value) {
      const dbInternalId = video.dbId || video.id;
      if (!dbInternalId) {
        continue;
      }

      try {
        // 먼저 내부 DB ID로 vss_videos 테이블에서 VIDEO_ID (VIA 서버의 video_id) 조회
        const videosResponse = await fetch(`${API_BASE_URL}/videos?user_id=${userId}`);
        if (videosResponse.ok) {
          const videosData = await videosResponse.json();
          if (videosData.success && videosData.videos) {
            const dbVideo = videosData.videos.find(v => v.id === dbInternalId);
            if (dbVideo && dbVideo.video_id) {
              // VIDEO_ID (VIA 서버의 video_id)로 요약 결과 조회
              const response = await fetch(`${API_BASE_URL}/summaries/${dbVideo.video_id}?user_id=${userId}`);
              if (response.ok) {
                try {
                  const data = await response.json();
                  
                  // data가 null이거나 undefined인 경우 처리
                  if (data && data.success && data.summary) {
                    // 요약 결과를 동영상 객체에 저장
                    video.summary = data.summary.summary_text;
                    
                    // 프롬프트가 있으면 prompt에 설정 (첫 번째 요약 결과의 프롬프트만 사용)
                    if (data.summary.prompt && !prompt.value) {
                      prompt.value = data.summary.prompt;
                    }
                    
                    // 요약된 비디오 ID 매핑 업데이트 (VIA 서버의 video_id 사용)
                    summarizedVideoMap.value[video.id] = dbVideo.video_id;
                    summarizedVideoId.value = dbVideo.video_id;
                    
                    // 채팅 메시지에 요약 결과 추가 (이미 표시되지 않은 경우)
                    const existingSummary = chatMessages.value.find(
                      m => m.role === 'assistant' && 
                           (m.content.includes(`'${video.name}'`) || m.content.includes(`'${video.title || ''}'`))
                    );
                    if (!existingSummary) {
                      const markedsummary = marked.parse(data.summary.summary_text);
                      const videoName = video.name || video.title || '동영상';
                      const summaryHtml = `<div class='font-semibold'>✅ '${videoName}' 요약 (저장된 결과)</div><br>${markedsummary}`;
                      addChatMessage({
                        id: Date.now() + Math.random(),
                        role: 'assistant',
                        content: summaryHtml
                      });
                    }
                  }
                } catch (jsonError) {
                  // JSON 파싱 실패 또는 null 응답 처리
                  console.warn(`동영상 ${dbInternalId}의 요약 결과 파싱 실패:`, jsonError);
                }
              } else {
                console.warn(`[loadSummariesFromDB] 요약 결과 조회 실패: HTTP ${response.status}`);
              }
            }
          }
        }
      } catch (error) {
        console.warn(`동영상 ${dbInternalId}의 요약 결과 로드 실패:`, error);
      }
    }
  } catch (error) {
    console.warn('요약 결과 로드 중 오류:', error);
  }
}

// localStorage 키 생성 함수 (사용자 ID 기반)
function getStorageKey() {
  const userId = localStorage.getItem("vss_user_id");
  if (!userId) {
    return 'summarize_page_state_no_user';
  }
  return `summarize_page_state_${userId}`;
}

// 상태를 localStorage에 저장하는 함수
function saveStateToLocalStorage() {
  try {
    const userId = localStorage.getItem("vss_user_id");
    if (!userId) {
      console.warn('사용자 ID가 없어 상태를 저장할 수 없습니다.');
      return;
    }

    const state = {
      // 사용자 ID 저장 (복원 시 검증용)
      userId: userId,
      // 동영상 정보 (File 객체는 제외하고 메타데이터만 저장)
      videoFiles: videoFiles.value.map(v => ({
        id: v.id,
        name: v.name,
        originUrl: v.originUrl,
        date: v.date,
        summary: v.summary || '',
        // File 객체는 저장하지 않음 (summaryVideoStore에 저장됨)
      })),
      // 프롬프트 및 요약 결과
      prompt: prompt.value,
      response: response.value,
      // 채팅 메시지
      chatMessages: chatMessages.value,
      // 질문 입력
      ask_prompt: ask_prompt.value,
      // 요약된 비디오 ID 매핑
      summarizedVideoId: summarizedVideoId.value,
      summarizedVideoMap: summarizedVideoMap.value,
      // 선택된 동영상 ID
      selectedIndexes: selectedIndexes.value,
      // 확대 상태
      isZoomed: isZoomed.value,
      zoomedIndex: zoomedIndex.value,
      // 스트리밍 상태
      streaming: streaming.value,
      // 실행 중인 작업 정보
      activeTasks: activeTasks.value.map(task => ({
        taskId: task.taskId,
        type: task.type,
        startTime: task.startTime,
        currentIndex: task.currentIndex,
        totalCount: task.totalCount,
        videoIds: task.videoIds,
        loadingIds: task.loadingIds,
        prompt: task.prompt || task.query,
        query: task.query,
        // File 객체는 저장하지 않음
      })),
      // 저장 시간
      savedAt: new Date().toISOString()
    };
    const storageKey = getStorageKey();
    localStorage.setItem(storageKey, JSON.stringify(state));
  } catch (e) {
    console.warn('localStorage 저장 실패:', e);
  }
}

// localStorage에서 상태를 복원하는 함수
function restoreStateFromLocalStorage() {
  try {
    const currentUserId = localStorage.getItem("vss_user_id");
    if (!currentUserId) {
      return false;
    }

    const storageKey = getStorageKey();
    const saved = localStorage.getItem(storageKey);
    if (!saved) return false;

    const state = JSON.parse(saved);
    
    // 저장된 사용자 ID와 현재 사용자 ID 비교
    if (state.userId && state.userId !== currentUserId) {
      // 다른 사용자의 상태는 삭제하지 않고 그대로 두고, 복원만 하지 않음
      return false;
    }
    
    // 프롬프트 및 요약 결과 복원
    if (state.prompt) prompt.value = state.prompt;
    if (state.response) response.value = state.response;
    
    // 채팅 메시지 복원
    if (Array.isArray(state.chatMessages)) {
      chatMessages.value = state.chatMessages;
      nextTick(() => scrollChatToBottom());
    }
    
    // 질문 입력 복원
    if (state.ask_prompt) ask_prompt.value = state.ask_prompt;
    
    // 요약된 비디오 ID 매핑 복원
    if (state.summarizedVideoId) summarizedVideoId.value = state.summarizedVideoId;
    if (state.summarizedVideoMap) summarizedVideoMap.value = state.summarizedVideoMap;
    
    // 선택된 동영상 ID 복원
    if (Array.isArray(state.selectedIndexes)) {
      selectedIndexes.value = state.selectedIndexes;
    }
    
    // 확대 상태 복원
    if (typeof state.isZoomed === 'boolean') isZoomed.value = state.isZoomed;
    if (state.zoomedIndex !== null && state.zoomedIndex !== undefined) {
      zoomedIndex.value = state.zoomedIndex;
    }
    
    // 스트리밍 상태 복원
    if (typeof state.streaming === 'boolean') streaming.value = state.streaming;
    
    // 실행 중인 작업 복원
    if (Array.isArray(state.activeTasks) && state.activeTasks.length > 0) {
      // 복원된 작업을 activeTasks에 추가하고 계속 실행
      nextTick(async () => {
        for (const savedTask of state.activeTasks) {
          if (savedTask.type === 'inference') {
            // runInference 작업 복원
            await restoreAndContinueInference(savedTask);
          } else if (savedTask.type === 'ask') {
            // onAsk 작업 복원
            await restoreAndContinueAsk(savedTask);
          }
        }
      });
    }
    
    // 동영상 정보 복원 (summaryVideoStore에서 File 객체를 가져와야 함)
    if (Array.isArray(state.videoFiles) && state.videoFiles.length > 0) {
      // 현재 사용자의 동영상만 필터링 (비동기이므로 여기서는 일단 복원하고, onMounted에서 필터링)
      // summaryVideoStore의 videos와 병합하여 복원
      const restoredVideos = state.videoFiles.map(savedVideo => {
        // summaryVideoStore에서 해당 ID의 동영상 찾기
        const storeVideo = summaryVideoStore.videos.find(v => v.id === savedVideo.id);
        const hasFile = storeVideo && storeVideo.file instanceof File;
        let summaryObjectUrl = null;
        // displayUrl 우선순위: summaryObjectUrl > savedVideo.originUrl > storeVideo.displayUrl > storeVideo.originUrl > storeVideo.url
        let displayUrl = savedVideo.originUrl || (storeVideo ? (storeVideo.displayUrl || storeVideo.originUrl || storeVideo.url) : '');
        
        if (hasFile) {
          // File 객체가 있으면 새로운 ObjectURL 생성
          summaryObjectUrl = URL.createObjectURL(storeVideo.file);
          displayUrl = summaryObjectUrl;
        } else if (savedVideo.originUrl) {
          // File 객체가 없으면 원본 URL 사용 (나중에 restoreMissingFile로 복원 시도)
          displayUrl = savedVideo.originUrl;
        } else if (storeVideo) {
          // storeVideo의 displayUrl 또는 originUrl 사용
          displayUrl = storeVideo.displayUrl || storeVideo.originUrl || storeVideo.url || '';
        }
        
        const originUrl = savedVideo.originUrl || (storeVideo ? (storeVideo.originUrl || storeVideo.url || displayUrl) : displayUrl);
        
        return {
          id: savedVideo.id,
          name: savedVideo.name,
          originUrl,
          displayUrl,
          summaryObjectUrl,
          date: savedVideo.date || (storeVideo ? storeVideo.date : ''),
          summary: savedVideo.summary || (storeVideo ? storeVideo.summary : ''),
          file: hasFile ? storeVideo.file : null
        };
      });
      
      videoFiles.value = restoredVideos;
      
      // File 객체가 없는 동영상은 URL에서 복원 시도
      nextTick(() => {
        restoreAllMissingFiles().then(() => {
          // 복원 후 ObjectURL 재생성
          videoFiles.value.forEach(video => {
            if (video.file instanceof File && !video.summaryObjectUrl) {
              video.summaryObjectUrl = URL.createObjectURL(video.file);
              video.displayUrl = video.summaryObjectUrl;
            }
          });
          
          // 복원된 동영상이 있으면 추천 chunk_size 계산
          setTimeout(() => {
            videoFiles.value.forEach(video => {
              updateRecommendedChunkSize(video.id);
            });
          }, 1000);
        });
      });
    }
    
    return true;
  } catch (e) {
    console.warn('localStorage 복원 실패:', e);
    return false;
  }
}

/**
 * 상태 변경 감지하여 자동 저장 (debounce 적용)
 */
let saveTimeout = null;
function autoSaveState() {
  if (saveTimeout) clearTimeout(saveTimeout);
  saveTimeout = setTimeout(() => {
    saveStateToLocalStorage();
  }, AUTO_SAVE_DELAY);
}

// 주요 상태 변경 감지
watch([prompt, response, chatMessages, ask_prompt, selectedIndexes, videoFiles, activeTasks], () => {
  autoSaveState();
}, { deep: true });

// Summarize 페이지에서 벗어날 때 상태 저장
onUnmounted(() => {
  document.removeEventListener('click', handleGlobalClick);
  window.removeEventListener('profile-menu-opened', closeContextMenu);
  
  // 페이지를 벗어나기 전에 상태 저장
  saveStateToLocalStorage();
  
  // 진행 중인 작업은 전역 관리자에 등록되어 있으므로 계속 실행됨
  // 타이머는 유지하지 않음 (페이지 전환 시 UI 업데이트가 불가능하므로)
  // 하지만 fetch 요청은 계속 진행되며, 완료 시 결과가 전역 저장소에 저장됨
  
  // Summarize에서 만든 전용 ObjectURL만 해제 (원본은 유지)
  videoFiles.value.forEach(v => {
    if (v.summaryObjectUrl) {
      try { URL.revokeObjectURL(v.summaryObjectUrl); } catch (_) { }
    }
  });
  
  // summaryVideoStore는 유지 (다른 페이지에서도 사용 가능)
  // clearVideos() 호출 제거 - 상태 유지를 위해
});

// watch 제거: 매 변경마다 새 ObjectURL 생성되어 누수 가능성 감소

function onDragOver(e) {
  isDragging.value = true;
}
function onDragLeave(e) {
  isDragging.value = false;
}
async function onDrop(e) {
  isDragging.value = false;
  const files = filterVideoFiles(e.dataTransfer.files);
  if (files.length === 0) return;

  // 사용자 ID 확인
  const userId = localStorage.getItem("vss_user_id");
  if (!userId) {
    alert('로그인이 필요합니다.');
    return;
  }

  // DB에서 중복 파일명 체크
  if (await checkDuplicateFiles(files, userId)) {
    return;
  }

  // 업로드 진행률 초기화
  uploadProgress.value = files.map((file, index) => ({
    id: Date.now() + index,
    fileName: file.name,
    progress: 0,
    status: '대기 중...',
    uploaded: 0,
    total: file.size
  }));

  // 업로드 모달 표시
  showUploadModal.value = true;

  // 서버에 동영상 업로드 (각 동영상이 완료되는 대로 즉시 표시)
  files.forEach(async (file, index) => {
    const uploadId = uploadProgress.value[index].id;
    try {
      const data = await uploadVideoWithProgress(file, userId, uploadId);
      
      const newVideo = createVideoObject({
        id: data.video_id,
        video_id: data.video_id,
        originUrl: data.file_url,
        url: data.file_url
      }, file);
      newVideo.name = file.name;
      newVideo.fileSize = file.size;

      // 업로드 완료된 동영상을 즉시 목록에 추가
      videoFiles.value.push(newVideo);
      
      // 지원하지 않는 형식인 경우 MP4로 변환 요청 (비동기로 실행)
      if (isUnsupportedFormat(file.name)) {
        convertVideoToMp4(data.video_id, userId, newVideo).then(convertedUrl => {
          if (convertedUrl) {
            console.log('동영상 변환 완료, 미리보기 업데이트:', file.name);
          }
        }).catch(error => {
          console.error('동영상 변환 실패:', error);
        });
      }
      
      // 지원하지 않는 형식인 경우 MP4로 변환 요청 (비동기로 실행)
      if (isUnsupportedFormat(file.name)) {
        convertVideoToMp4(data.video_id, userId, newVideo).then(convertedUrl => {
          if (convertedUrl) {
            console.log('동영상 변환 완료, 미리보기 업데이트:', file.name);
          }
        }).catch(error => {
          console.error('동영상 변환 실패:', error);
        });
      }
      
      // 프로그레스 바를 100%로 업데이트 (리스트에 추가된 후)
      const uploadItem = uploadProgress.value.find(u => u.id === uploadId);
      if (uploadItem) {
        uploadItem.progress = 100;
        uploadItem.status = '완료';
      }
      
      // Search.vue에 이벤트 전달하여 동영상 목록 새로고침
      window.dispatchEvent(new CustomEvent('search-videos-updated'));
      
      // summaryVideoStore 업데이트
      const storeVideos = videoFiles.value.map(v => ({
        id: v.id,
        title: v.name,
        name: v.name,
        url: v.originUrl || v.displayUrl,
        originUrl: v.originUrl,
        displayUrl: v.displayUrl,
        objectUrl: v.summaryObjectUrl,
        date: v.date,
        file: v.file,
        summary: v.summary || '',
        dbId: v.dbId
      }));
      summaryVideoStore.setVideos(storeVideos);
      
      // 동영상 업로드 시 streaming을 true로 설정
      streaming.value = true;
      
      // 동영상이 DOM에 추가된 후 길이를 가져와서 추천 chunk_size 계산
      nextTick(() => {
        setTimeout(() => {
          updateRecommendedChunkSize(newVideo.id);
        }, UPLOAD_PROCESSING_DELAY);
      });
    } catch (error) {
      // 업로드 취소는 정상적인 동작이므로 에러로 처리하지 않음
      if (error.message === '업로드 취소됨') {
        return; // 조용히 종료
      }
      console.error('동영상 업로드 실패:', error);
      const uploadItem = uploadProgress.value.find(u => u.id === uploadId);
      if (uploadItem) {
        uploadItem.status = `실패: ${error.message}`;
      }
    }
  });

  if (videoFiles.value.length > 0 && selectedIndexes.value.length === 0) {
    selectedIndexes.value = videoFiles.value.map(v => v.id);
  }
}

function onVideoAreaClick() {
  // Only open file picker when there are no uploaded videos.
  if (videoFiles.value && videoFiles.value.length > 0) return;
  if (fileInputRef.value) fileInputRef.value.click();
}

function selectVideo(id) {
  closeContextMenu();
  const idx = selectedIndexes.value.indexOf(id);
  if (idx === -1) {
    selectedIndexes.value.push(id);
  } else {
    selectedIndexes.value.splice(idx, 1);
  }
}

function closeContextMenu() {
  contextMenu.value.visible = false;
  contextMenu.value.video = null;
  contextMenu.value.index = null;
}

function onVideoContextMenu(video, idx, event) {
  if (!video) return;
  event.preventDefault();
  event.stopPropagation();
  if (selectedIndexes.value.length < 2) {
    if (!selectedIndexes.value.includes(video.id)) {
      selectedIndexes.value = [video.id];
    }
  }

  // 다른 메뉴들에게 비디오 컨텍스트 메뉴가 열릴 예정임을 먼저 알림 (다른 메뉴를 닫기 위해)
  window.dispatchEvent(new CustomEvent('video-context-menu-opened'));

  // 마우스 포인터 위치를 직접 사용
  const x = event.clientX;
  const y = event.clientY;

  contextMenu.value = {
    visible: true,
    x: x,
    y: y,
    video,
    index: idx
  };
}

function handleGlobalClick(e) {
  // 우클릭 이벤트는 무시 (컨텍스트 메뉴가 열릴 수 있음)
  if (e && (e.button === 2 || e.which === 3)) return;
  
  if (!contextMenu.value.visible) return;
  closeContextMenu();
}

function contextZoom() {
  const { index, video } = contextMenu.value;
  closeContextMenu();
  if (index != null && index >= 0) {
    zoomVideo(index);
    return;
  }
  if (video) {
    const resolvedIndex = videoFiles.value.findIndex(v => v.id === video.id);
    if (resolvedIndex !== -1) {
      zoomVideo(resolvedIndex);
    }
  }
}

function contextOpenSettings() {
  closeContextMenu();
  showSettingModal.value = true;
}

async function contextDelete() {
  const { video } = contextMenu.value;
  closeContextMenu();
  if (!video) return;
  if (!selectedIndexes.value.includes(video.id) || selectedIndexes.value.length < 2) {
    selectedIndexes.value = [video.id];
  }
  if (selectedIndexes.value.length === 0) return;
  await batchRemoveSelectedVideos();
}

function zoomVideo(idx) {
  if (idx == null || idx < 0 || idx >= videoFiles.value.length) return;
  zoomedIndex.value = idx;
  isZoomed.value = true;
}

function unzoomVideo() {
  isZoomed.value = false;
  zoomedIndex.value = null;
}

async function onUpload(e) {
  const files = filterVideoFiles(e.target.files ?? []);
  if (!files.length) return;

  // 사용자 ID 확인
  const userId = localStorage.getItem("vss_user_id");
  if (!userId) {
    alert('로그인이 필요합니다.');
    return;
  }

  // DB에서 중복 파일명 체크
  if (await checkDuplicateFiles(files, userId)) {
          if (fileInputRef.value) fileInputRef.value.value = '';
          return;
  }

  // 업로드 진행률 초기화
  uploadProgress.value = files.map((file, index) => ({
    id: Date.now() + index,
    fileName: file.name,
    progress: 0,
    status: '대기 중...',
    uploaded: 0,
    total: file.size
  }));

  // 업로드 모달 표시
  showUploadModal.value = true;

  // 서버에 동영상 업로드 (각 동영상이 완료되는 대로 즉시 표시)
  files.forEach(async (file, index) => {
    const uploadId = uploadProgress.value[index].id;
    try {
      const data = await uploadVideoWithProgress(file, userId, uploadId);
      
      const newVideo = createVideoObject({
        id: data.video_id,
        video_id: data.video_id,
        originUrl: data.file_url,
        url: data.file_url
      }, file);
      newVideo.name = file.name;
      newVideo.fileSize = file.size;

      // 업로드 완료된 동영상을 즉시 목록에 추가
      videoFiles.value.unshift(newVideo);
      
      // 지원하지 않는 형식인 경우 MP4로 변환 요청 (비동기로 실행)
      if (isUnsupportedFormat(file.name)) {
        convertVideoToMp4(data.video_id, userId, newVideo).then(convertedUrl => {
          if (convertedUrl) {
            console.log('동영상 변환 완료, 미리보기 업데이트:', file.name);
          }
        }).catch(error => {
          console.error('동영상 변환 실패:', error);
        });
      }
      
      // 프로그레스 바를 100%로 업데이트 (리스트에 추가된 후)
      const uploadItem = uploadProgress.value.find(u => u.id === uploadId);
      if (uploadItem) {
        uploadItem.progress = 100;
        uploadItem.status = '완료';
      }
      
      // Search.vue에 이벤트 전달하여 동영상 목록 새로고침
      window.dispatchEvent(new CustomEvent('search-videos-updated'));
      
      // summaryVideoStore 업데이트
      const storeVideos = videoFiles.value.map(v => ({
        id: v.id,
        title: v.name,
        name: v.name,
        url: v.originUrl || v.displayUrl,
        originUrl: v.originUrl,
        displayUrl: v.displayUrl,
        objectUrl: v.summaryObjectUrl,
        date: v.date,
        file: v.file,
        summary: v.summary || '',
        dbId: v.dbId
      }));
      summaryVideoStore.setVideos(storeVideos);
      
      // 동영상 업로드 시 streaming을 true로 설정
      streaming.value = true;

      // 업로드된 동영상에 대해 추천 chunk_size 계산
      nextTick(() => {
        setTimeout(() => {
          updateRecommendedChunkSize(newVideo.id);
        }, UPLOAD_PROCESSING_DELAY);
      });
    } catch (error) {
      // 업로드 취소는 정상적인 동작이므로 에러로 처리하지 않음
      if (error.message === '업로드 취소됨') {
        return; // 조용히 종료
      }
      console.error('동영상 업로드 실패:', error);
      const uploadItem = uploadProgress.value.find(u => u.id === uploadId);
      if (uploadItem) {
        uploadItem.status = `실패: ${error.message}`;
      }
    }
  });

  // input[type=file] value 초기화
  if (fileInputRef.value) fileInputRef.value.value = '';
  if (videoFiles.value.length > 0 && selectedIndexes.value.length === 0) {
    selectedIndexes.value = videoFiles.value.map(v => v.id);
  }
}

// 실행 중인 Ask 작업 복원 및 계속 진행
async function restoreAndContinueAsk(savedTask) {
  const taskId = savedTask.taskId;
  const query = savedTask.query || savedTask.prompt;
  
  if (!query) {
    console.warn('복원할 질문을 찾을 수 없습니다.');
    return;
  }
  
  // 작업 상태 업데이트
  const taskIndex = activeTasks.value.findIndex(t => t.taskId === taskId);
  if (taskIndex === -1) {
    activeTasks.value.push({
      taskId,
      type: 'ask',
      startTime: savedTask.startTime || Date.now(),
      query: query
    });
  }
  
  // 질문 계속 진행
  await onAskConfirmed(query);
  
  // 작업 완료
  const finalTaskIndex = activeTasks.value.findIndex(t => t.taskId === taskId);
  if (finalTaskIndex !== -1) {
    activeTasks.value.splice(finalTaskIndex, 1);
  }
}

// 실행 중인 작업 복원 및 계속 진행
async function restoreAndContinueInference(savedTask) {
  const taskId = savedTask.taskId;
  const currentIndex = savedTask.currentIndex || 0;
  const totalCount = savedTask.totalCount;
  const videoIds = savedTask.videoIds || [];
  
  // 동영상 객체 복원
  const targetVideos = videoIds.map(id => videoFiles.value.find(v => v.id === id)).filter(Boolean);
  
  if (targetVideos.length === 0) {
    console.warn('복원할 동영상을 찾을 수 없습니다.');
    return;
  }
  
  // 작업 상태 업데이트
  const taskIndex = activeTasks.value.findIndex(t => t.taskId === taskId);
  if (taskIndex === -1) {
    activeTasks.value.push({
      taskId,
      type: 'inference',
      startTime: savedTask.startTime,
      currentIndex,
      totalCount,
      videoIds,
      loadingIds: [],
      prompt: savedTask.prompt
    });
  }
  
  // 중단된 지점부터 계속 실행
  await continueInferenceFromIndex(taskId, targetVideos, currentIndex, totalCount, savedTask.prompt);
}

/**
 * 특정 인덱스부터 요약 계속 진행 (백그라운드에서 계속 실행)
 */
async function continueInferenceFromIndex(taskId, targetVideos, startIndex, totalCount, taskPrompt) {
  const VSS_API_URL = `${API_BASE_URL}/vss-summarize`;
  
  // 전역 작업 관리자에 등록 (페이지 전환 후에도 계속 실행되도록)
  const taskInfo = {
    taskId,
    type: 'inference',
    startTime: Date.now(),
    currentIndex: startIndex,
    totalCount,
    videoIds: targetVideos.map(v => v.id),
    videoNames: targetVideos.map(v => v.name || v.title),
    prompt: taskPrompt,
    status: 'running',
    completedVideos: [],
    failedVideos: []
  };
  window.__vssActiveTasks.set(taskId, taskInfo);
  
  // 작업 상태를 localStorage에 저장 (주기적으로 업데이트)
  const updateTaskState = () => {
    const taskState = {
      taskId,
      type: 'inference',
      startTime: taskInfo.startTime,
      currentIndex: taskInfo.currentIndex,
      totalCount,
      videoIds: taskInfo.videoIds,
      videoNames: taskInfo.videoNames,
      prompt: taskPrompt,
      completedVideos: taskInfo.completedVideos,
      failedVideos: taskInfo.failedVideos
    };
    const userId = localStorage.getItem("vss_user_id");
    if (userId) {
      const storageKey = `vss_active_task_${userId}_${taskId}`;
      localStorage.setItem(storageKey, JSON.stringify(taskState));
    }
  };
  
  // NaN 방지 헬퍼
  const safeNum = (val, fallback) => {
    const n = Number(val);
    return Number.isFinite(n) ? n : fallback;
  };
  
  for (let idx = startIndex; idx < targetVideos.length; idx++) {
    const videoObj = targetVideos[idx];
    
    // 작업 상태 업데이트 (로컬 및 전역)
    const currentTask = activeTasks.value.find(t => t.taskId === taskId);
    if (currentTask) {
      currentTask.currentIndex = idx;
    }
    if (taskInfo) {
      taskInfo.currentIndex = idx;
      updateTaskState();
    }
    
    // File 복원 시도
    if (videoObj && !(videoObj.file instanceof File)) {
      await restoreMissingFile(videoObj);
    }
    if (!videoObj || !(videoObj.file instanceof File)) {
      addChatMessage({
        id: Date.now() + Math.random(),
        role: 'system',
        content: `❌ '${videoObj?.name || 'Unnamed'}' 파일 객체를 확보하지 못했습니다. 건너뜁니다.`
      });
      continue;
    }

    const loadingId = Date.now() + Math.random();
    
    // 로딩 메시지 추가 (페이지가 활성화된 경우에만)
    if (document.visibilityState === 'visible') {
      addChatMessage({
        id: loadingId,
        role: 'system',
        content: `⏳ [${idx + 1}/${totalCount}] '${videoObj.name}' 요약 요청 중...`
      });
    }
    
    // 로딩 ID 저장
    if (currentTask) {
      currentTask.loadingIds.push(loadingId);
    }
    
    const startTime = Date.now();

    // DB에서 VIA 서버의 video_id 조회
    const userId = localStorage.getItem("vss_user_id");
    let viaVideoId = null;
    
    if (userId && videoObj.dbId) {
      try {
        const videosResponse = await fetch(`${API_BASE_URL}/videos?user_id=${userId}`);
        if (videosResponse.ok) {
          const videosData = await videosResponse.json();
          if (videosData.success && videosData.videos) {
            const video = videosData.videos.find(v => v.id === videoObj.dbId);
            if (video && video.video_id) {
              viaVideoId = video.video_id; // vss_videos 테이블의 VIDEO_ID 컬럼 (VIA 서버의 video_id)
            }
          }
        }
      } catch (error) {
        console.warn('VIA video_id 조회 실패:', error);
      }
    }
    
    if (!viaVideoId) {
      addChatMessage({
        id: Date.now() + Math.random(),
        role: 'system',
        content: `❌ '${videoObj?.name || 'Unnamed'}'의 VIA 서버 video_id를 찾을 수 없습니다. 동영상을 먼저 업로드해주세요.`
      });
      continue;
    }

    const formData = new FormData();
    formData.append('file', videoObj.file);
    formData.append('prompt', taskPrompt ?? prompt.value ?? '');
    formData.append('csprompt', settingStore.captionPrompt ?? '');
    formData.append('saprompt', settingStore.aggregationPrompt ?? '');
    formData.append('chunk_duration', safeNum(settingStore.chunk, 10));
    formData.append('num_frames_per_chunk', safeNum(settingStore.nfmc, 1));
    formData.append('frame_width', safeNum(settingStore.frameWidth, 224));
    formData.append('frame_height', safeNum(settingStore.frameHeight, 224));
    formData.append('top_k', safeNum(settingStore.topk, 1));
    formData.append('top_p', safeNum(settingStore.topp, 1.0));
    formData.append('temperature', safeNum(settingStore.temp, 1.0));
    formData.append('max_tokens', safeNum(settingStore.maxTokens, 512));
    formData.append('seed', safeNum(settingStore.seed, 1));
    formData.append('batch_size', safeNum(settingStore.batch, 6));
    formData.append('rag_batch_size', safeNum(settingStore.RAG_batch, 1));
    formData.append('rag_top_k', safeNum(settingStore.RAG_topk, 1));
    formData.append('summary_top_p', safeNum(settingStore.S_TopP, 1.0));
    formData.append('summary_temperature', safeNum(settingStore.S_TEMPERATURE, 1.0));
    formData.append('summary_max_tokens', safeNum(settingStore.SMAX_TOKENS, 512));
    formData.append('chat_top_p', safeNum(settingStore.C_TopP, 1.0));
    formData.append('chat_temperature', safeNum(settingStore.C_TEMPERATURE, 1.0));
    formData.append('chat_max_tokens', safeNum(settingStore.C_MAX_TOKENS, 512));
    formData.append('alert_top_p', safeNum(settingStore.A_TopP, 1.0));
    formData.append('alert_temperature', safeNum(settingStore.A_TEMPERATURE, 1.0));
    formData.append('alert_max_tokens', safeNum(settingStore.A_MAX_TOKENS, 512));
    formData.append('enable_audio', settingStore.enableAudio ? true : false);
    formData.append('video_id', viaVideoId); // VIA 서버의 video_id 전달

    // 경과 시간 추적기 설정 (페이지가 활성화된 경우에만 UI 업데이트)
    const intervalId = setInterval(() => {
      if (document.visibilityState === 'visible') {
        const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
        const loadingIdx = chatMessages.value.findIndex(m => m.id === loadingId);
        if (loadingIdx !== -1) {
          chatMessages.value[loadingIdx].content = `⏳ [${idx + 1}/${totalCount}] '${videoObj.name}' 요약 요청 중... (경과 시간: ${elapsed}s)`;
        }
      }
    }, 100); // 0.1초마다 업데이트 (소수점 실시간 표시)
    
    // 타이머 저장 (페이지가 활성화된 경우에만)
    if (document.visibilityState === 'visible') {
      activeIntervals.value[loadingId] = intervalId;
      
      // 작업 상태에 타이머 정보 저장
      if (currentTask) {
        if (!currentTask.intervals) currentTask.intervals = [];
        currentTask.intervals.push({ loadingId, intervalId, startTime });
      }
    }

    try {
      const res = await fetch(VSS_API_URL, { method: 'POST', body: formData });
      
      // 타이머 정리 (설정된 경우에만)
      if (intervalId) {
        clearInterval(intervalId);
      }
      if (activeIntervals.value[loadingId]) {
        delete activeIntervals.value[loadingId];
      }
      
      // 작업 상태에서 타이머 제거
      if (currentTask && currentTask.intervals) {
        const intervalIdx = currentTask.intervals.findIndex(i => i.loadingId === loadingId);
        if (intervalIdx !== -1) currentTask.intervals.splice(intervalIdx, 1);
      }
      
      const endTime = Date.now();
      const elapsed = ((endTime - startTime) / 1000).toFixed(2);
      if (!res.ok) {
        let errText = await res.text();
        const errHtml = `❌ [${idx + 1}/${totalCount}] '${videoObj.name}' 실패 (HTTP ${res.status})<br><code>${errText}</code><br><div class='text-xs text-gray-500'>시간: ${elapsed}s`;
        
        // 실패한 작업 정보 저장
        if (taskInfo) {
          taskInfo.failedVideos.push({
            videoId: videoObj.id,
            videoName: videoObj.name,
            error: errText
          });
          updateTaskState();
        }
        
        // UI 업데이트 (컴포넌트가 활성화된 경우에만)
        if (document.visibilityState === 'visible') {
          const loadingIdx = chatMessages.value.findIndex(m => m.id === loadingId);
          if (loadingIdx !== -1) chatMessages.value.splice(loadingIdx, 1);
          addChatMessage({ id: Date.now() + Math.random(), role: 'system', content: errHtml });
        }
        console.error('Summarization error response:', errText);
        continue;
      }
      const data = await res.json();
      const serverVideoId = data.video_id;
      const summaryText = data.summary || '';
      summarizedVideoMap.value[videoObj.id] = serverVideoId;
      summarizedVideoId.value = serverVideoId;
      
      // 요약 결과를 동영상 객체에 저장 (videoFiles.value에서 찾아서 업데이트)
      const videoInFiles = videoFiles.value.find(v => v.id === videoObj.id);
      if (videoInFiles) {
        videoInFiles.summary = summaryText;
      }
      // videoObj에도 저장 (참조가 같은 경우를 대비)
      videoObj.summary = summaryText;
      
      const markedsummary = marked.parse(summaryText);
      const summaryHtml = `<div class='font-semibold'>✅ [${idx + 1}/${totalCount}] '${videoObj.name}' 요약 완료</div><br>${markedsummary}<br><div class='text-xs text-gray-500'>시간: ${elapsed}s | 서버 ID: ${serverVideoId}</div>`;
      response.value = summaryHtml;
      
      // 작업 완료 결과 저장 (페이지 전환 후에도 결과를 받을 수 있도록)
      const resultKey = `vss_task_result_${taskId}_${videoObj.id}`;
      window.__vssTaskResults.set(resultKey, {
        taskId,
        videoId: videoObj.id,
        videoName: videoObj.name,
        summaryText,
        summaryHtml,
        serverVideoId,
        elapsed,
        index: idx + 1,
        totalCount,
        timestamp: Date.now()
      });
      
      // 전역 작업 정보 업데이트
      if (taskInfo) {
        taskInfo.completedVideos.push({
          videoId: videoObj.id,
          videoName: videoObj.name,
          serverVideoId,
          summaryText
        });
        updateTaskState();
      }
      
      // UI 업데이트 (컴포넌트가 활성화된 경우에만)
      if (document.visibilityState === 'visible') {
        const loadingIdx = chatMessages.value.findIndex(m => m.id === loadingId);
        if (loadingIdx !== -1) chatMessages.value.splice(loadingIdx, 1);
        addChatMessage({ id: Date.now() + Math.random(), role: 'assistant', content: summaryHtml });
      }
      
      // DB에 요약 결과 저장
      const userId = localStorage.getItem("vss_user_id");
      if (userId) {
        try {
          // vss_videos 테이블의 VIDEO_ID 컬럼 (VIA 서버의 video_id) 찾기
          let dbVideoId = null;
          
          // 먼저 videoObj.dbId로 동영상 찾기
          let dbInternalId = videoObj.dbId;
          
          if (!dbInternalId) {
            // 파일명으로 DB에서 내부 ID 찾기
            try {
              const videosResponse = await fetch(`${API_BASE_URL}/videos?user_id=${userId}`);
              if (videosResponse.ok) {
                const videosData = await videosResponse.json();
                if (videosData.success && videosData.videos) {
                  const video = videosData.videos.find(v => v.title === videoObj.name);
                  if (video) {
                    dbInternalId = video.id;
                    // videoObj에 dbId 저장 (다음 요약 시 재사용)
                    videoObj.dbId = dbInternalId;
                  }
                }
              }
            } catch (error) {
              console.warn('동영상 목록 조회 실패:', error);
            }
          }
          
          // 내부 ID로 vss_videos 테이블에서 VIDEO_ID 컬럼 (VIA 서버의 video_id) 가져오기
          if (dbInternalId) {
            try {
              const videosResponse = await fetch(`${API_BASE_URL}/videos?user_id=${userId}`);
              if (videosResponse.ok) {
                const videosData = await videosResponse.json();
                if (videosData.success && videosData.videos) {
                  const video = videosData.videos.find(v => v.id === dbInternalId);
                  if (video && video.video_id) {
                    dbVideoId = video.video_id; // vss_videos 테이블의 VIDEO_ID 컬럼 (VIA 서버의 video_id)
                  }
                }
              }
            } catch (error) {
              console.warn('VIDEO_ID 조회 실패:', error);
            }
          }
          
          if (dbVideoId) {
            const saveResponse = await fetch(`${API_BASE_URL}/save-summary`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                video_id: dbVideoId,
                user_id: userId,
                prompt: taskPrompt ?? prompt.value ?? '',
                summary_text: summaryText,
                via_video_id: serverVideoId  // VIA 서버의 video_id 저장
              })
            });
            
            if (saveResponse.ok) {
              await saveResponse.json();
            } else {
              const errorData = await saveResponse.json().catch(() => ({ detail: '알 수 없는 오류' }));
              console.warn('요약 결과 저장 실패:', errorData);
            }
          } else {
            console.warn(`요약 결과 저장 실패: 동영상 ID를 찾을 수 없습니다. (파일명: ${videoObj.name})`);
          }
        } catch (error) {
          console.warn('요약 결과 저장 중 오류:', error);
        }
      } else {
        console.warn('요약 결과 저장 실패: 사용자 ID가 없습니다.');
      }
    } catch (e) {
      // 타이머 정리 (설정된 경우에만)
      if (intervalId) {
        clearInterval(intervalId);
      }
      if (activeIntervals.value[loadingId]) {
        delete activeIntervals.value[loadingId];
      }
      
      // 작업 상태에서 타이머 제거
      if (currentTask && currentTask.intervals) {
        const intervalIdx = currentTask.intervals.findIndex(i => i.loadingId === loadingId);
        if (intervalIdx !== -1) currentTask.intervals.splice(intervalIdx, 1);
      }
      
      const endTime = Date.now();
      const elapsed = ((endTime - startTime) / 1000).toFixed(2);
      const errHtml = `❌ [${idx + 1}/${totalCount}] '${videoObj.name}' 네트워크 오류: ${(e && e.message) || 'unknown'}<br><div class='text-xs text-gray-500'>시간: ${elapsed}s</div>`;
      
      // 실패한 작업 정보 저장
      if (taskInfo) {
        taskInfo.failedVideos.push({
          videoId: videoObj.id,
          videoName: videoObj.name,
          error: (e && e.message) || 'unknown'
        });
        updateTaskState();
      }
      
      // UI 업데이트 (컴포넌트가 활성화된 경우에만)
      if (document.visibilityState === 'visible') {
        const loadingIdx = chatMessages.value.findIndex(m => m.id === loadingId);
        if (loadingIdx !== -1) chatMessages.value.splice(loadingIdx, 1);
        addChatMessage({ id: Date.now() + Math.random(), role: 'system', content: errHtml });
      }
      console.error('Summarization request failed:', e);
    }
    
    // 로딩 ID 제거
    if (currentTask) {
      const lidx = currentTask.loadingIds.indexOf(loadingId);
      if (lidx !== -1) currentTask.loadingIds.splice(lidx, 1);
    }
  }
  
  // 작업 완료 처리
  taskInfo.status = 'completed';
  taskInfo.completedAt = Date.now();
  updateTaskState();
  
  // 전역 작업 관리자에서 제거 (결과는 __vssTaskResults에 저장됨)
  window.__vssActiveTasks.delete(taskId);
  
  // localStorage에서 작업 상태 제거
  const userId = localStorage.getItem("vss_user_id");
  if (userId) {
    const storageKey = `vss_active_task_${userId}_${taskId}`;
    localStorage.removeItem(storageKey);
  }
  
  // 로컬 작업 목록에서 제거
  const taskIndex = activeTasks.value.findIndex(t => t.taskId === taskId);
  if (taskIndex !== -1) {
    activeTasks.value.splice(taskIndex, 1);
  }
  
  // 전체 완료 메시지 (컴포넌트가 활성화된 경우에만)
  if (document.visibilityState === 'visible') {
    addChatMessage({
      id: Date.now() + Math.random(),
      role: 'system',
      content: `✅ 모든 요약 처리 완료 (${taskInfo.completedVideos.length}개 성공). 질의 시 선택된 영상의 서버 요약을 우선 사용합니다.`
    });
  }
  
  // 작업 완료 이벤트 발생 (다른 컴포넌트에서도 감지 가능)
  window.dispatchEvent(new CustomEvent('vss-task-completed', {
    detail: { taskId, taskInfo }
  }));
}

async function runInference() {
  // Prompt이 없을 경우 경고 모달 표시
  if (!prompt.value || String(prompt.value).trim().length === 0) {
    // 사용자에게 입력을 요구하고 실행을 막기 위한 단순 경고
    warningMessage.value = '텍스트를 입력하십시오.';
    pendingAction = null;
    showWarningModal.value = true;
    return;
  }

  // 순차 처리 대상: 선택된 것이 있으면 선택 영상들, 없으면 전체
  const targetVideos = (selectedIndexes.value.length > 0)
    ? videoFiles.value.filter(v => selectedIndexes.value.includes(v.id))
    : [...videoFiles.value];

  if (targetVideos.length === 0) {
    alert('요약할 동영상이 없습니다.');
    return;
  }

  // 작업 ID 생성
  const taskId = Date.now() + Math.random();
  const taskPrompt = prompt.value;
  
  // 작업 상태 저장
  activeTasks.value.push({
    taskId,
    type: 'inference',
    startTime: Date.now(),
    currentIndex: 0,
    totalCount: targetVideos.length,
    videoIds: targetVideos.map(v => v.id),
    loadingIds: [],
    prompt: taskPrompt
  });

  // NaN 방지 헬퍼
  const safeNum = (val, fallback) => {
    const n = Number(val);
    return Number.isFinite(n) ? n : fallback;
  };

  // 진행 상태 집계 표시
  addChatMessage({
    id: Date.now() + Math.random(),
    role: 'system',
    content: `📦 총 ${targetVideos.length}개 동영상 요약을 시작합니다.`
  });

  // 작업 시작
  await continueInferenceFromIndex(taskId, targetVideos, 0, targetVideos.length, taskPrompt);
}

// 동영상이 1개일 때 삭제
async function removeSingleVideo() {
  if (videoFiles.value.length === 1) {
    const target = videoFiles.value[0];

    // 매핑에서 제거 (미디어 삭제는 Search.vue에서 처리)
    if (summarizedVideoMap.value[target.id]) {
      delete summarizedVideoMap.value[target.id];
    }

    if (target.summaryObjectUrl) {
      try { URL.revokeObjectURL(target.summaryObjectUrl); } catch (_) { }
    }
    // 재생 중 목록 정리
    const playIdx = playingVideoIds.value.indexOf(target.id);
    if (playIdx !== -1) playingVideoIds.value.splice(playIdx, 1);
    videoFiles.value = [];
    selectedIndexes.value = [];
    isZoomed.value = false;
    zoomedIndex.value = null;
    // 재생 상태 및 레퍼런스 초기화
    hoveredVideoId.value = null;
    playingVideoIds.value = [];
    videoRefs.value = {};
    // 프롬프트 텍스트 초기화
    prompt.value = "";
    // 요약 결과도 초기화
    response.value = '';
    chatMessages.value = [];
    // 스토어도 즉시 비움 (다시 방문 시 재로드 방지)
    if (summaryVideoStore && typeof summaryVideoStore.clearVideos === 'function') {
      summaryVideoStore.clearVideos();
    } else if (summaryVideoStore && typeof summaryVideoStore.setVideos === 'function') {
      summaryVideoStore.setVideos([]);
    }
    // 동영상이 없으면 streaming을 false로 설정
    streaming.value = false;
  }
}

// 경고 모달 상태/메시지
const showWarningModal = ref(false);
const warningMessage = ref('');
let pendingAction = null; // function to execute if user confirms

function closeWarning() {
  showWarningModal.value = false;
  warningMessage.value = '';
  pendingAction = null;
}

function confirmWarning() {
  // 단순히 모달을 닫기만 함 (실행 금지)
  showWarningModal.value = false;
  pendingAction = null;
  warningMessage.value = '';
}


async function batchRemoveSelectedVideos() {
  const videosToRemove = videoFiles.value.filter(v => selectedIndexes.value.includes(v.id));

  // 매핑에서 제거 (미디어 삭제는 Search.vue에서 처리)
  videosToRemove.forEach(v => {
    if (summarizedVideoMap.value[v.id]) {
      delete summarizedVideoMap.value[v.id];
    }
  });

  videosToRemove.forEach(v => {
    if (v.summaryObjectUrl) {
      try { URL.revokeObjectURL(v.summaryObjectUrl); } catch (_) { }
    }
    const playIdx = playingVideoIds.value.indexOf(v.id);
    if (playIdx !== -1) playingVideoIds.value.splice(playIdx, 1);
    // 개별 videoRefs 제거
    if (videoRefs.value[v.id]) delete videoRefs.value[v.id];
  });
  videoFiles.value = videoFiles.value.filter(v => !selectedIndexes.value.includes(v.id));
  selectedIndexes.value = [];
  // 프롬프트 텍스트 항상 초기화 (부분 삭제도 포함)
  prompt.value = "";
  // 요약 결과도 초기화 (부분 삭제 포함 전체 삭제 시 동일하게 초기화)
  response.value = '';
  chatMessages.value = [];
  // 동영상이 없으면 streaming을 false로 설정
  streaming.value = videoFiles.value.length > 0;
  if (videoFiles.value.length === 0) {
    isZoomed.value = false;
    zoomedIndex.value = null;
    hoveredVideoId.value = null;
    playingVideoIds.value = [];
    videoRefs.value = {};
  }
}

async function onAsk(q) {
  if (!q || String(q).trim().length === 0) {
    // 사용자에게 입력을 요구하고 실행을 막기 위한 단순 경고
    warningMessage.value = '텍스트를 입력하십시오.';
    pendingAction = null;
    showWarningModal.value = true;
    return;
  }
  await onAskConfirmed(q);
}

async function onAskConfirmed(q) {
  // 작업 ID 생성
  const taskId = Date.now() + Math.random();
  
  // 작업 상태 저장
  activeTasks.value.push({
    taskId,
    type: 'ask',
    startTime: Date.now(),
    query: q
  });
  
  const VSS_API_URL = `${API_BASE_URL}/vss-query`;
  const formData = new FormData();

  const safeNum = (val, fallback) => {
    const n = Number(val);
    return Number.isFinite(n) ? n : fallback;
  };

  const firstSelectedId = selectedIndexes.value[0];
  let videoObj = videoFiles.value.find(v => v.id === firstSelectedId) || videoFiles.value[0];

  // 다중 요약 대응: 선택된 첫 영상이 매핑되어 있으면 그것 사용, 없으면 마지막 요약 ID
  let serverVideoIdForQuery = null;
  if (selectedIndexes.value.length > 0) {
    const localId = selectedIndexes.value[0];
    serverVideoIdForQuery = summarizedVideoMap.value[localId];
  }
  if (!serverVideoIdForQuery) serverVideoIdForQuery = summarizedVideoId.value;

  if (serverVideoIdForQuery) {
    formData.append('video_id', serverVideoIdForQuery);
  } else {
    // File 복원 시도
    if (videoObj && !(videoObj.file instanceof File)) {
      await restoreMissingFile(videoObj);
    }
    if (!videoObj || !(videoObj.file instanceof File)) {
      alert('선택된(또는 첫 번째) 동영상의 File 객체를 확보하지 못했습니다. 다시 업로드 후 시도하세요.');
      // 작업 제거
      const taskIndex = activeTasks.value.findIndex(t => t.taskId === taskId);
      if (taskIndex !== -1) activeTasks.value.splice(taskIndex, 1);
      return;
    }
    formData.append('file', videoObj.file);
  }
  formData.append('query', q ?? ask_prompt.value ?? '');
  formData.append('chunk_size', safeNum(settingStore.chunk, 10));
  formData.append('top_k', safeNum(settingStore.topk, 1));
  formData.append('top_p', safeNum(settingStore.topp, 1.0));
  formData.append('temperature', safeNum(settingStore.temp, 1.0));
  formData.append('max_new_tokens', safeNum(settingStore.maxTokens, 512));
  formData.append('seed', safeNum(settingStore.seed, 1));

  // 사용자가 입력한 질문을 채팅창에 추가
  addChatMessage({ id: Date.now() + Math.random(), role: 'user', content: q });

  try {
    const res = await fetch(VSS_API_URL, { method: 'POST', body: formData });
    if (!res.ok) {
      alert(`질의 요청 실패 (HTTP ${res.status})`);
      // 작업 제거
      const taskIndex = activeTasks.value.findIndex(t => t.taskId === taskId);
      if (taskIndex !== -1) activeTasks.value.splice(taskIndex, 1);
      return;
    }
    const data = await res.json();
    const markedanswer = marked.parse(data.summary || '');
    const answerHtml = `<div class='font-semibold'>✅ Query Answered</div><br>${markedanswer}`;
    addChatMessage({ id: Date.now() + Math.random(), role: 'assistant', content: answerHtml });
  } catch (e) {
    console.error('질의 요청 실패:', e);
    addChatMessage({ 
      id: Date.now() + Math.random(), 
      role: 'system', 
      content: `❌ 질의 요청 중 네트워크 오류: ${(e && e.message) || 'unknown'}` 
    });
  } finally {
    // 작업 완료
    const taskIndex = activeTasks.value.findIndex(t => t.taskId === taskId);
    if (taskIndex !== -1) {
      activeTasks.value.splice(taskIndex, 1);
    }
  }
}

function clear() {
  prompt.value = "";
  response.value = "";
  chatMessages.value = [];
  ask_prompt.value = "";
  summarizedVideoId.value = null;
  summarizedVideoMap.value = {};
  scrollChatToBottom();
  // localStorage도 초기화 (사용자별 키 사용)
  const storageKey = getStorageKey();
  localStorage.removeItem(storageKey);
}

function copyMessage(m) {
  try {
    const tmp = document.createElement('div');
    tmp.innerHTML = m.content || '';
    const text = tmp.innerText.trim();
    navigator.clipboard.writeText(text);
    addChatMessage({ role: 'system', content: '📋 메시지가 클립보드에 복사되었습니다.' });
  } catch (e) {
    console.warn('Copy failed', e);
    addChatMessage({ role: 'system', content: '❌ 복사 실패: 권한 또는 브라우저 제한.' });
  }
}

function togglePlay(videoId) {
  const el = videoRefs.value[videoId];
  if (!el) {
    // 삭제 후 남은 stale id 정리
    const ghostIdx = playingVideoIds.value.indexOf(videoId);
    if (ghostIdx !== -1) playingVideoIds.value.splice(ghostIdx, 1);
    return;
  }
  // 다중 재생 허용: 기존 재생 중인 다른 비디오를 중지하지 않음
  // playingVideoIds 배열은 재생 중인 모든 비디오 id를 유지
  const idx = playingVideoIds.value.indexOf(videoId);
  if (idx === -1) {
    el.play();
    playingVideoIds.value.push(videoId);
  } else {
    el.pause();
    playingVideoIds.value.splice(idx, 1);
  }
}

function onVideoEnded(videoId) {
  const idx = playingVideoIds.value.indexOf(videoId);
  if (idx !== -1) playingVideoIds.value.splice(idx, 1);
}

// 시간 포맷터 (mm:ss)
function formatTime(sec) {
  if (!Number.isFinite(sec)) return '00:00';
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
}

// 파일 크기 포맷터
function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

// 업로드 모달 닫기 (X 버튼 클릭 시 업로드 중단)
function closeUploadModal() {
  // 진행 중인 모든 업로드 취소
  Object.keys(activeUploads.value).forEach(uploadId => {
    const xhr = activeUploads.value[uploadId];
    if (xhr && xhr.readyState !== XMLHttpRequest.DONE) {
      xhr.abort(); // 업로드 중단
      const uploadItem = uploadProgress.value.find(u => u.id === uploadId);
      if (uploadItem && uploadItem.progress < 100) {
        uploadItem.status = '취소됨';
        uploadItem.progress = 0;
      }
    }
  });
  
  // 활성 업로드 목록 초기화
  activeUploads.value = {};
  
  // 모달 닫기 및 진행률 초기화
  showUploadModal.value = false;
  uploadProgress.value = [];
}

// 모든 업로드 완료 여부
const allUploadsComplete = computed(() => {
  return uploadProgress.value.length > 0 && 
         uploadProgress.value.every(u => u.progress === 100 || u.status === '완료' || u.status === '실패');
});

// XMLHttpRequest를 사용한 업로드 함수 (진행률 추적)
function uploadVideoWithProgress(file, userId, uploadId) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId);

    // 활성 업로드 목록에 추가 (취소 가능하도록)
    activeUploads.value[uploadId] = xhr;

    // 진행률 업데이트 (99%까지만 표시)
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        const rawProgress = Math.round((e.loaded / e.total) * 100);
        // 99%까지만 표시 (리스트에 추가되기 전까지)
        const progress = Math.min(rawProgress, 99);
        const uploadItem = uploadProgress.value.find(u => u.id === uploadId);
        if (uploadItem) {
          uploadItem.progress = progress;
          uploadItem.uploaded = e.loaded;
          uploadItem.total = e.total;
          uploadItem.status = '업로드 중...';
        }
      }
    });

    // 완료 처리 (99%에서 멈춤, 리스트 추가 후 100%로 변경)
    xhr.addEventListener('load', () => {
      // 활성 업로드 목록에서 제거
      delete activeUploads.value[uploadId];
      
      if (xhr.status === 200) {
        try {
          const data = JSON.parse(xhr.responseText);
          const uploadItem = uploadProgress.value.find(u => u.id === uploadId);
          if (uploadItem) {
            uploadItem.progress = 99; // 99%에서 멈춤
            uploadItem.status = '처리 중...';
          }
          resolve(data);
        } catch (e) {
          const uploadItem = uploadProgress.value.find(u => u.id === uploadId);
          if (uploadItem) {
            uploadItem.status = '실패';
          }
          reject(new Error('응답 파싱 실패'));
        }
      } else {
        const uploadItem = uploadProgress.value.find(u => u.id === uploadId);
        if (uploadItem) {
          uploadItem.status = '실패';
        }
        reject(new Error(`업로드 실패: ${xhr.status}`));
      }
    });

    // 에러 처리
    xhr.addEventListener('error', () => {
      // 활성 업로드 목록에서 제거
      delete activeUploads.value[uploadId];
      
      const uploadItem = uploadProgress.value.find(u => u.id === uploadId);
      if (uploadItem) {
        uploadItem.status = '실패';
      }
      reject(new Error('네트워크 오류'));
    });

    // 중단(abort) 처리
    xhr.addEventListener('abort', () => {
      // 활성 업로드 목록에서 제거
      delete activeUploads.value[uploadId];
      
      const uploadItem = uploadProgress.value.find(u => u.id === uploadId);
      if (uploadItem) {
        uploadItem.status = '취소됨';
      }
      reject(new Error('업로드 취소됨'));
    });

    xhr.open('POST', `${API_BASE_URL}/upload-video`);
    xhr.send(formData);
  });
}

async function saveResult() {
  // 상태를 localStorage에 저장
  saveStateToLocalStorage();
  
  // 요약 결과 수집: videoFiles의 summary 속성과 chatMessages에서 추출
  const videosWithSummary = [];
  
  // 1. videoFiles에서 summary 속성이 있는 동영상 수집
  for (const video of videoFiles.value) {
    if (video.summary && video.summary.trim()) {
      videosWithSummary.push({
        ...video,
        summaryText: video.summary
      });
    }
  }
  
  // 2. chatMessages에서 요약 결과 추출 (videoFiles에 summary가 없는 경우)
  if (videosWithSummary.length === 0) {
    // chatMessages에서 assistant 메시지의 요약 결과 추출
    const summaryMessages = chatMessages.value.filter(m => 
      m.role === 'assistant' && 
      m.content && 
      (m.content.includes('요약 완료') || m.content.includes('요약 (저장된 결과)'))
    );
    
    if (summaryMessages.length > 0) {
      // chatMessages에서 동영상 이름과 요약 내용 추출
      for (const msg of summaryMessages) {
        // HTML에서 텍스트 추출 (marked로 파싱된 HTML에서 원본 텍스트 추출)
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = msg.content;
        const textContent = tempDiv.textContent || tempDiv.innerText || '';
        
        // 동영상 이름 추출 (예: '동영상명' 요약 완료)
        const videoNameMatch = textContent.match(/'([^']+)'/);
        if (videoNameMatch) {
          const videoName = videoNameMatch[1];
          const video = videoFiles.value.find(v => 
            (v.name && v.name.includes(videoName)) || 
            (v.title && v.title.includes(videoName))
          );
          
          if (video) {
            // HTML에서 요약 텍스트 추출 (marked HTML 제거)
            const summaryText = extractSummaryFromHtml(msg.content);
            if (summaryText && summaryText.trim()) {
              video.summary = summaryText;
              if (!videosWithSummary.find(v => v.id === video.id)) {
                videosWithSummary.push({
                  ...video,
                  summaryText: summaryText
                });
              }
            }
          }
        }
      }
    }
  }
  
  // 3. 전역 작업 결과에서 요약 결과 추출
  if (videosWithSummary.length === 0 && window.__vssTaskResults) {
    for (const [resultKey, result] of window.__vssTaskResults.entries()) {
      if (result.summaryText && result.videoId) {
        const video = videoFiles.value.find(v => v.id === result.videoId);
        if (video && !videosWithSummary.find(v => v.id === video.id)) {
          video.summary = result.summaryText;
          videosWithSummary.push({
            ...video,
            summaryText: result.summaryText
          });
        }
      }
    }
  }
  
  if (videosWithSummary.length === 0) {
  addChatMessage({
    id: Date.now() + Math.random(),
    role: 'system',
      content: '⚠️ 저장할 요약 결과가 없습니다. 먼저 요약을 실행해주세요.'
    });
    return;
  }
  
  // 보고서 내용 생성
  const reportContent = generateReportContent(videosWithSummary);
  
  // 보고서 제목 생성 (날짜 기반)
  const now = new Date();
  const dateStr = now.toLocaleDateString(settingStore.language === 'ko' ? 'ko-KR' : 'en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
  const reportTitle = settingStore.language === 'ko' 
    ? `요약 보고서 - ${dateStr}`
    : `Summary Report - ${dateStr}`;
  
  // 단어 수 계산
  const wordCount = reportContent.split(/\s+/).filter(word => word.length > 0).length;
  
  // 보고서 객체 생성
  const report = {
    id: Date.now(),
    title: reportTitle,
    description: settingStore.language === 'ko' 
      ? `${videosWithSummary.length}개의 동영상 요약 결과`
      : `Summary results for ${videosWithSummary.length} videos`,
    content: reportContent,
    createdAt: now.toISOString(),
    wordCount: wordCount,
    videoIds: videosWithSummary.map(v => v.id),
    videoTitles: videosWithSummary.map(v => v.name || v.title || 'Unknown')
  };
  
  // 보고서 저장 (API 또는 localStorage)
  const userId = localStorage.getItem("vss_user_id");
  if (userId) {
    try {
      // API로 보고서 저장 시도
      const response = await fetch(`${API_BASE_URL}/reports`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          title: report.title,
          description: report.description,
          content: report.content,
          word_count: report.wordCount,
          video_ids: report.videoIds,
          video_titles: report.videoTitles
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.report_id) {
          report.id = data.report_id;
          addChatMessage({
            id: Date.now() + Math.random(),
            role: 'system',
            content: '💾 보고서가 성공적으로 생성되었습니다. 리포트 메뉴에서 확인할 수 있습니다.'
          });
          return;
        }
      }
    } catch (error) {
      console.warn('보고서 API 저장 실패, localStorage에 저장:', error);
    }
  }
  
  // API 저장 실패 시 localStorage에 저장
  const reportsKey = `vss_reports_${userId || 'guest'}`;
  const existingReports = JSON.parse(localStorage.getItem(reportsKey) || '[]');
  existingReports.unshift(report); // 최신 보고서를 맨 앞에 추가
  localStorage.setItem(reportsKey, JSON.stringify(existingReports));
  
  addChatMessage({
    id: Date.now() + Math.random(),
    role: 'system',
    content: '💾 보고서가 생성되었습니다. 리포트 메뉴에서 확인할 수 있습니다.'
  });
}

// HTML에서 순수 텍스트 요약 추출 함수
function extractSummaryFromHtml(htmlContent) {
  const tempDiv = document.createElement('div');
  tempDiv.innerHTML = htmlContent;
  
  // '요약 완료' 또는 '요약 (저장된 결과)' 텍스트 제거
  const textContent = tempDiv.textContent || tempDiv.innerText || '';
  
  // 동영상 이름과 "요약 완료" 텍스트 제거
  let summaryText = textContent
    .replace(/✅\s*\[?\d+\/?\d*\]?\s*'[^']+'\s*요약\s*(완료|\(저장된 결과\))/g, '')
    .replace(/시간:\s*\d+\.\d+s/g, '')
    .replace(/서버\s*ID:\s*\d+/g, '')
    .trim();
  
  // 빈 줄 정리
  summaryText = summaryText.replace(/\n{3,}/g, '\n\n');
  
  return summaryText;
}

// 보고서 내용 생성 함수
function generateReportContent(videos) {
  const lines = [];
  
  // 헤더
  lines.push('# 요약 보고서\n');
  lines.push(`생성일: ${new Date().toLocaleDateString(settingStore.language === 'ko' ? 'ko-KR' : 'en-US')}\n`);
  lines.push(`동영상 수: ${videos.length}개\n`);
  lines.push('---\n');
  
  // 각 동영상별 요약
  videos.forEach((video, index) => {
    const videoName = video.name || video.title || `동영상 ${index + 1}`;
    const summaryText = video.summaryText || video.summary || '';
    
    if (!summaryText.trim()) return; // 요약이 없으면 건너뛰기
    
    lines.push(`\n## ${index + 1}. ${videoName}\n`);
    if (video.date) {
      lines.push(`**날짜:** ${video.date}\n`);
    }
    lines.push('\n');
    lines.push(summaryText);
    lines.push('\n');
    lines.push('---\n');
  });
  
  return lines.join('\n');
}
</script>

<style scoped>
.chat-row {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  animation: fadeIn 0.25s ease;
}

.chat-row.from-user {
  justify-content: flex-end;
}

.avatar {
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  background: #d1d5db;
  color: #111827;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.avatar-user {
  background: #10b981;
  color: #fff;
}

.avatar-assistant {
  background: #10b981;
  color: #fff;
}

.avatar-system {
  background: #6b7280;
  color: #fff;
}

.chat-bubble {
  max-width: 70%;
  background: #ffffff;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  position: relative;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.chat-bubble.assistant {
  background: #ffffff;
}

.chat-bubble.user {
  background: #ecfdf5;
}

.chat-bubble.system {
  background: #f3f4f6;
  font-size: 13px;
}

.chat-bubble :deep(code) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
}

.chat-bubble :deep(pre) {
  background: #1e293b;
  color: #f8fafc;
  padding: 10px 12px;
  border-radius: 8px;
  overflow: auto;
  font-size: 13px;
}

.chat-bubble :deep(pre code) {
  background: transparent;
  padding: 0;
}

.chat-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
  color: #6b7280;
}

.chat-meta .time {
  user-select: none;
}

.copy-btn {
  background: transparent;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 2px 8px;
  font-size: 11px;
  cursor: pointer;
  color: #374151;
  transition: background 0.15s ease, color 0.15s ease;
}

.copy-btn:hover {
  background: #e5e7eb;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(4px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.brightness-75 {
  filter: brightness(75%);
  transition: filter 0.3s ease;
}

.chat-window {
  backdrop-filter: blur(2px);
}

.chat-row {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.chat-row:hover {
  transform: translateY(-2px);
}

.chat-bubble {
  transition: box-shadow 0.3s ease, background 0.3s ease;
}

.chat-bubble.assistant:hover {
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
}

.chat-bubble.user:hover {
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
}

.chat-bubble.system:hover {
  box-shadow: 0 4px 12px rgba(107, 114, 128, 0.25);
}

.transition-all {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
</style>
