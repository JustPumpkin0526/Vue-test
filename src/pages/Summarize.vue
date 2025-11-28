<template>
  <div class="grid lg:grid-cols-2 gap-6">
    <!-- 좌측: 비디오/업로드 -->
    <section class="rounded-2xl p-5 bg-gradient-to-br from-white via-gray-50 to-gray-100 border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-300">
      <div class="flex items-center gap-2 mb-3">
        <h2 class="font-semibold">
          {{ isZoomed ? (videoFiles[zoomedIndex]?.name || 'Video Section') : (videoFiles.length > 1 ? 'Video Section' : (videoFiles[0]?.name || 'Video Section')) }}
        </h2>
        <button @click="showSettingModal = true" title="설정" class="ml-auto w-9 h-9 flex items-center justify-center bg-white/90 hover:bg-white backdrop-blur-md rounded-full shadow transition-all duration-200 border border-gray-200">
          <img :src="settingIcon" alt="설정" class="w-5 h-5 object-contain" />
        </button>
      </div>


      <div
        class="aspect-video h-92 rounded-xl mb-3 flex items-center justify-center text-gray-600 transition-all cursor-pointer relative overflow-hidden group ring-1 ring-gray-300"
        :class="[isDragging ? 'bg-blue-50 ring-blue-300' : 'bg-gray-200']"
        @dragover.prevent="onDragOver" @dragleave.prevent="onDragLeave" @drop.prevent="onDrop"
        @click="onVideoAreaClick">
        <template v-if="!videoFiles || videoFiles.length === 0">
          <div v-if="sampleVideoPath" class="relative w-full h-full overflow-hidden rounded-xl">
            <!-- 원본 동영상 (중앙 선명) -->
            <video
              ref="sampleVideoRef"
              :src="sampleVideoPath"
              class="w-full h-full object-cover brightness-75"
              autoplay
              loop
              muted
              playsinline
              preload="auto"
              style="
                mask-image: radial-gradient(ellipse 95% 95% at center, black 0%, black 40%, rgba(0,0,0,0.8) 50%, rgba(0,0,0,0.4) 60%, transparent 100%);
                -webkit-mask-image: radial-gradient(ellipse 95% 95% at center, black 0%, black 40%, rgba(0,0,0,0.8) 50%, rgba(0,0,0,0.4) 60%, transparent 100%);
              "
            ></video>
            <!-- 블러 처리된 동영상 (가장자리) -->
            <video
              :src="sampleVideoPath"
              class="absolute inset-0 w-full h-full object-cover brightness-75"
              autoplay
              loop
              muted
              playsinline
              preload="auto"
              style="
                filter: blur(25px);
                mask-image: radial-gradient(ellipse 95% 95% at center, transparent 0%, transparent 40%, rgba(0,0,0,0.2) 50%, rgba(0,0,0,0.4) 60%, rgba(0,0,0,0.6) 70%, rgba(0,0,0,0.8) 85%, black 100%);
                -webkit-mask-image: radial-gradient(ellipse 95% 95% at center, transparent 0%, transparent 40%, rgba(0,0,0,0.2) 50%, rgba(0,0,0,0.4) 60%, rgba(0,0,0,0.6) 70%, rgba(0,0,0,0.8) 85%, black 100%);
              "
            ></video>
            <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
              <span v-if="!isDragging" class="font-bold text-white drop-shadow-lg text-center px-4">
                Drop Video here<br>-- or --<br>Click to upload
              </span>
              <span v-else class="text-white font-bold drop-shadow-lg">여기에 파일을 놓으세요</span>
            </div>
          </div>
          <span v-else-if="!isDragging" class="font-bold text-blue-500 flex flex-col items-center justify-center text-center w-full">
            Drop Video here<br>-- or --<br>Click to upload
          </span>
          <span v-else class="text-blue-600 font-bold">여기에 파일을 놓으세요</span>
        </template>
        <template v-else-if="videoFiles.length === 1">
          <div class="relative w-full h-full" @mouseenter="singleVideo && (hoveredVideoId = singleVideo.id)"
            @mouseleave="hoveredVideoId = null">
            <video v-if="singleVideo" :src="singleVideo.displayUrl" class="w-full h-full rounded-xl object-cover transition-opacity duration-300"
              preload="metadata" :ref="el => { if (el && singleVideo) videoRefs[singleVideo.id] = el }"
              @timeupdate="updateProgress(singleVideo.id, $event)"
              @ended="singleVideo && onVideoEnded(singleVideo.id)"
              :class="{ 'brightness-75': !playingVideoIds.includes(singleVideo.id) }"></video>
            <!-- 정지 시 어두운 오버레이 -->
            <div v-if="singleVideo" class="absolute inset-0 pointer-events-none transition-colors duration-300"
              :class="playingVideoIds.includes(singleVideo.id) ? 'bg-transparent' : 'bg-black/40'"></div>
            <!-- 하단 오버레이 진행바 & 시간 (overflow-hidden 영역 내에서 겹쳐 표시) -->
            <div v-if="singleVideo" 
              class="absolute bottom-0 left-0 right-0 p-2 bg-black/30 backdrop-blur-sm rounded-b-xl transition-all duration-300 pointer-events-none"
              :class="{
                'opacity-100 translate-y-0': hoveredVideoId === singleVideo.id || !playingVideoIds.includes(singleVideo.id),
                'opacity-0 translate-y-full': hoveredVideoId !== singleVideo.id && playingVideoIds.includes(singleVideo.id)
              }">
              <div class="flex flex-col gap-1">
                <div
                  class="w-full h-2 bg-gray-300/70 rounded-full relative cursor-pointer pointer-events-auto overflow-visible"
                  @click.stop="seekVideo(singleVideo.id, $event)"
                  :ref="el => { if (el && singleVideo) progressBarRefs[singleVideo.id] = el }">
                  <div
                    :class="[
                      'h-full bg-gradient-to-r from-blue-500 to-indigo-500',
                      (isScrubbing && draggingVideoId === singleVideo.id)
                        ? 'transition-none'
                        : 'transition-[width] duration-150 ease-linear'
                    ]"
                    :style="{ width: `${progress[singleVideo.id] || 0}%` }"></div>
                  <div
                    class="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white rounded-full border border-blue-500 cursor-pointer shadow hover:shadow-md hover:scale-110 transition-all pointer-events-auto"
                    :style="{ left: `calc(${progress[singleVideo.id] || 0}% - 8px)` }"
                    @mousedown="startDragging(singleVideo.id, $event)"
                    @click.stop
                  ></div>
                </div>
                <div class="flex justify-between text-[10px] font-medium text-gray-200 tracking-wide px-1 pointer-events-auto">
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
              <svg v-else xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 16 16" class="w-10 h-10">
                <path
                  d="M5.5 3.5A.5.5 0 0 1 6 3h1a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5H6a.5.5 0 0 1-.5-.5v-9zM9.5 3.5A.5.5 0 0 1 10 3h1a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-9z" />
              </svg>
            </button>
          </div>
        </template>
        <template v-else>
          <!-- 여러 개일 때 리스트 & 확대 분기 -->
          <div v-if="!isZoomed" id="list" class="relative w-full h-full border border-gray-200 bg-gradient-to-br from-white to-gray-50 rounded-2xl p-6 mt-0 shadow-inner">
            <div class="w-full h-[100%] border border-gray-200 bg-white rounded-2xl overflow-y-auto shadow-sm">
              <div class="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-3 gap-6 p-6">
                <div v-for="(video, idx) in videoFiles" :key="video.id"
                  class="flex flex-col items-center justify-center rounded-2xl shadow-md hover:shadow-xl cursor-pointer p-3 border border-gray-200 relative transform transition-all duration-300 hover:scale-105 hover:-translate-y-1 group"
                  :class="{ 'ring-2 ring-blue-400 bg-blue-100': selectedIndexes.includes(video.id) }"
                  @click="selectVideo(video.id)"
                  @contextmenu.prevent.stop="onVideoContextMenu(video, idx, $event)">
                  <div
                    class="flex items-center justify-center bg-gray-200 rounded-xl overflow-hidden relative group"
                    @mouseenter="hoveredVideoId = video.id" @mouseleave="hoveredVideoId = null">
                    <input type="checkbox" class="absolute top-1 left-1 z-10" v-model="selectedIndexes"
                      :value="video.id" />
                    <video v-if="video.displayUrl" :src="video.displayUrl" class="object-cover rounded-xl transition-opacity duration-300"
                      preload="metadata" :ref="el => (videoRefs[video.id] = el)" @ended="onVideoEnded(video.id)"
                      @timeupdate="updateProgress(video.id, $event)"
                      :class="{ 'brightness-75': !playingVideoIds.includes(video.id) }"></video>
                    <div v-if="video.displayUrl" class="absolute inset-0 pointer-events-none transition-colors duration-300"
                      :class="playingVideoIds.includes(video.id) ? 'bg-transparent' : 'bg-black/30'">
                    </div>
                    <span v-else class="text-gray-400">No Thumbnail</span>
                    <div v-if="video.title || video.name"
                      class="absolute top-1 right-1 bg-gradient-to-r from-black/70 to-black/50 backdrop-blur-sm text-white text-xs px-2.5 py-2 rounded-lg truncate max-w-[70%] pointer-events-none shadow-lg leading-[1.6] z-30 overflow-visible">
                      <span class="relative">{{ video.title || video.name }}</span>
                    </div>
                    <!-- 오버레이 진행바 & 시간 (멀티 비디오용) -->
                    <div v-if="video.displayUrl" 
                      class="absolute bottom-0 left-0 right-0 p-2 bg-black/30 backdrop-blur-sm rounded-b-xl transition-all duration-300 pointer-events-none"
                      :class="{
                        'opacity-100 translate-y-0': hoveredVideoId === video.id || !playingVideoIds.includes(video.id),
                        'opacity-0 translate-y-full': hoveredVideoId !== video.id && playingVideoIds.includes(video.id)
                      }">
                      <div class="flex flex-col gap-1">
                        <div
                          class="w-full h-2 bg-gray-300/70 rounded-full relative cursor-pointer pointer-events-auto backdrop-blur-sm overflow-visible"
                          @click.stop="seekVideo(video.id, $event)"
                          :ref="el => { if (el) progressBarRefs[video.id] = el }">
                          <div
                            :class="[
                              'h-full bg-gradient-to-r from-blue-500 to-indigo-500',
                              (isScrubbing && draggingVideoId === video.id)
                                ? 'transition-none'
                                : 'transition-[width] duration-150 ease-linear'
                            ]"
                            :style="{ width: `${progress[video.id] || 0}%` }"></div>
                          <div
                            class="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full border border-blue-500 cursor-pointer shadow hover:shadow-md hover:scale-110 transition-all pointer-events-auto"
                            :style="{ left: `calc(${progress[video.id] || 0}% - 6px)` }"
                            @mousedown="startDragging(video.id, $event)"
                            @click.stop></div>
                        </div>
                        <div class="flex justify-between text-[10px] font-medium text-gray-200 tracking-wide px-1 pointer-events-auto">
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
                </div>
              </div>
            </div>
            <!-- 우클릭 컨텍스트 메뉴 -->
            <div v-if="contextMenu.visible" class="fixed z-[200]"
              :style="{ left: `${contextMenu.x}px`, top: `${contextMenu.y}px` }" @click.stop>
              <div class="bg-white rounded-lg shadow-xl border border-gray-100 overflow-hidden w-[200px]">
                <button v-if="selectedIndexes.length < 2" class="w-full text-left px-4 py-3 hover:bg-gray-50" @click.stop="contextZoom">확대</button>
                <button class="w-full text-left px-4 py-3 hover:bg-gray-50" @click.stop="contextOpenSettings">설정</button>
                <div class="h-px bg-gray-100"></div>
                <button class="w-full text-left px-4 py-3 text-red-600 hover:bg-gray-50" @click.stop="contextDelete">
                  {{ selectedIndexes.length > 1 ? `선택된 항목 삭제 (${selectedIndexes.length})` : '삭제' }}
                </button>
              </div>
            </div>
          </div>
          <!-- 확대 뷰 -->
          <div v-else class="flex flex-col items-center w-full">
            <div class="relative w-full h-[100%] mb-2" @mouseenter="videoFiles[zoomedIndex] && (hoveredVideoId = videoFiles[zoomedIndex].id)" @mouseleave="hoveredVideoId = null">
              <!-- 닫기(X) 버튼 -->
              <button
                v-if="videoFiles[zoomedIndex]"
                @click.stop="unzoomVideo"
                aria-label="확대 종료"
                title="닫기"
                class="absolute top-2 right-2 z-20 w-8 h-8 flex items-center justify-center bg-black/50 hover:bg-black/70 rounded-full text-white shadow transition-all duration-200 hover:scale-110 active:scale-95"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" viewBox="0 0 24 24" class="w-5 h-5">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
              <video v-if="videoFiles[zoomedIndex]" :src="videoFiles[zoomedIndex].displayUrl"
                class="w-full h-[100%] rounded-xl object-cover transition-all duration-300" preload="metadata"
                :ref="el => { if (el && videoFiles[zoomedIndex]) videoRefs[videoFiles[zoomedIndex].id] = el }"
                @timeupdate="updateProgress(videoFiles[zoomedIndex].id, $event)"
                @ended="onVideoEnded(videoFiles[zoomedIndex].id)"
                :class="{ 'brightness-75': !playingVideoIds.includes(videoFiles[zoomedIndex].id) }"></video>
              <div v-if="videoFiles[zoomedIndex]" class="absolute inset-0 pointer-events-none transition-colors duration-300" :class="playingVideoIds.includes(videoFiles[zoomedIndex].id) ? 'bg-transparent' : 'bg-black/40'"></div>
              <div v-if="videoFiles[zoomedIndex]"
                class="absolute top-2 left-2 bg-gradient-to-r from-black/70 to-black/50 backdrop-blur-sm text-white text-xs px-2.5 py-2 rounded-lg truncate max-w-[70%] pointer-events-none shadow-lg leading-[1.6] z-30 overflow-visible">
                <span class="relative">{{ videoFiles[zoomedIndex].name || videoFiles[zoomedIndex].title }}</span>
              </div>
              <!-- 확대 뷰 재생 진행바 & 시간 (단일/멀티와 동일 스타일) -->
              <div v-if="videoFiles[zoomedIndex]" 
                class="absolute bottom-0 left-0 right-0 p-2 bg-black/30 backdrop-blur-sm rounded-b-xl transition-all duration-300 pointer-events-none"
                :class="{
                  'opacity-100 translate-y-0': hoveredVideoId === videoFiles[zoomedIndex].id || !playingVideoIds.includes(videoFiles[zoomedIndex].id),
                  'opacity-0 translate-y-full': hoveredVideoId !== videoFiles[zoomedIndex].id && playingVideoIds.includes(videoFiles[zoomedIndex].id)
                }">
                <div class="flex flex-col gap-1">
                  <div
                    class="w-full h-2 bg-gray-300/70 rounded-full relative cursor-pointer pointer-events-auto overflow-visible"
                    @click.stop="seekVideo(videoFiles[zoomedIndex].id, $event)"
                    :ref="el => { if (el && videoFiles[zoomedIndex]) progressBarRefs[videoFiles[zoomedIndex].id] = el }">
                    <div
                      :class="[
                        'h-full bg-gradient-to-r from-blue-500 to-indigo-500',
                        (isScrubbing && draggingVideoId === videoFiles[zoomedIndex].id)
                          ? 'transition-none'
                          : 'transition-[width] duration-150 ease-linear'
                      ]"
                      :style="{ width: `${progress[videoFiles[zoomedIndex].id] || 0}%` }"></div>
                    <div
                      class="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white rounded-full border border-blue-500 cursor-pointer shadow hover:shadow-md hover:scale-110 transition-all pointer-events-auto"
                      :style="{ left: `calc(${progress[videoFiles[zoomedIndex].id] || 0}% - 8px)` }"
                      @mousedown="startDragging(videoFiles[zoomedIndex].id, $event)"
                      @click.stop></div>
                  </div>
                  <div class="flex justify-between text-[10px] font-medium text-gray-200 tracking-wide px-1 pointer-events-auto">
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



      <!-- 프롬프트 입력 블럭 -->
      <div class="mb-3 flex items-center gap-2">
        <div class="relative flex-1">
          <textarea v-model="prompt" class="w-full border border-gray-300 focus:border-blue-400 focus:ring-2 focus:ring-blue-300 rounded-xl px-3 py-2 resize-none transition-all"
            placeholder="프롬프트를 입력하세요." rows="3" @keydown.enter.exact.prevent="runInference"></textarea>
          <button
            class="absolute right-[8px] top-[45px] p-2 rounded-lg bg-gradient-to-r from-blue-500 to-indigo-600 text-white flex items-center justify-center shadow hover:shadow-lg hover:from-blue-600 hover:to-indigo-700 transition-all duration-200"
            @click="runInference" :disabled="videoFiles.length === 0 || selectedIndexes.length === 0">
            <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0.4 -1 16 16" class="w-5 h-5">
              <path
                d="M6.271 4.055a.5.5 0 0 1 .759-.429l4.592 3.11a.5.5 0 0 1 0 .828l-4.592 3.11a.5.5 0 0 1-.759-.429V4.055z" />
            </svg>
          </button>
        </div>
      </div>

      <input type="file" accept="video/*" multiple @change="onUpload" ref="fileInputRef" class="hidden" />

          <!-- 경고 모달 -->
          <div v-if="showWarningModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
            <div class="bg-white rounded-lg shadow-lg max-w-lg w-full p-6">
              <h3 class="text-lg font-semibold mb-2">경고</h3>
              <p class="text-sm text-gray-700 mb-4" v-html="warningMessage"></p>
              <div class="flex justify-end gap-2">
                <button class="px-3 py-2 rounded bg-blue-600 text-white" @click="closeWarning">확인</button>
              </div>
            </div>
          </div>

      <div v-if="videoFiles.length === 1" class="mt-2 flex">
        <button
          @click="removeSingleVideo"
          class="relative flex items-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-br from-red-500 to-red-600 text-white font-medium shadow-lg hover:shadow-xl hover:from-red-600 hover:to-red-700 transition-all duration-300 transform hover:scale-105 active:scale-95"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.9" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 6h18" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M8 6V4.8c0-.442 0-.663.074-.842a1 1 0 01.418-.418C8.671 3.466 8.892 3.466 9.334 3.466h5.332c.442 0 .663 0 .842.074a1 1 0 01.418.418c.074.179.074.4.074.842V6m-6 5v5m4-5v5M5 6l1.2 12.4c.109 1.123.163 1.685.44 2.118a2 2 0 00.826.73c.458.222 1.021.222 2.147.222h4.374c1.126 0 1.689 0 2.147-.222a2 2 0 00.826-.73c.277-.433.331-.995.44-2.118L19 6" />
          </svg>
          <span>동영상 삭제</span>
        </button>
      </div>

      <p class="text-xs text-gray-500 mt-2">
        요약 성능을 조정하고 싶다면 우측 상단의 설정 버튼을 클릭하여 조정할 수 있습니다.
      </p>
      <!-- Setting Modal -->
      <div v-if="showSettingModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
        <div class="bg-white rounded-lg shadow-lg max-w-[90%] max-h-[90%] w-full p-4 overflow-auto">
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-semibold">설정</h3>
            <button @click="closeSettingModal" class="px-2 py-[1px] rounded-full border-[2px] border-gray-300 ">X</button>
          </div>
          <Setting />
        </div>
      </div>
    </section>

    <!-- 우측: 결과/프롬프트 -->
    <section class="rounded-2xl p-5 bg-gradient-to-br from-white via-gray-50 to-gray-100 border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-300">
      <h2 class="font-semibold mb-3">요약 결과</h2>
      <!-- 채팅 형태 출력 영역 -->
      <div class="chat-window border border-gray-200 rounded-xl bg-gradient-to-br from-gray-50 to-gray-100 h-[600px] p-3 overflow-auto shadow-inner" ref="chatWindowRef">
        <div v-if="chatMessages.length === 0" class="text-gray-400 text-sm flex items-center justify-center h-full">
          아직 메시지가 없습니다. 요약을 실행하거나 질문을 입력하세요.
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
              <div class="chat-meta" :class="{'justify-end': m.role==='user'}">
                <span class="time">{{ new Date(m.time).toLocaleTimeString() }}</span>
                <button v-if="m.role === 'assistant' || m.role === 'user'" class="copy-btn" @click="copyMessage(m)">복사</button>
              </div>
            </div>
          </div>
        </template>
      </div>

      <div class="flex items-center gap-2 mt-3">
        <input v-model="ask_prompt" placeholder="질문을 입력하세요..."
          class="w-full rounded-xl border border-gray-300 focus:border-green-500 focus:ring-2 focus:ring-green-300 px-4 py-3 bg-white transition-all"
          @keyup.enter="() => { onAsk(ask_prompt); ask_prompt = '';}" />
        <button class="rounded-lg bg-gradient-to-r from-green-500 to-green-600 text-white px-4 py-2 shadow hover:shadow-lg hover:from-green-600 hover:to-green-700 transition-all duration-200" @click="() => { onAsk(ask_prompt); ask_prompt = ''; }">
          Ask
        </button>
      </div>

      <div class="mt-3 flex gap-2">
        <button class="px-3 py-2 rounded-md bg-gradient-to-r from-gray-200 to-gray-300 text-gray-700 shadow hover:shadow-md hover:from-gray-300 hover:to-gray-400 transition-all duration-200" @click="saveResult">결과 저장</button>
        <button class="px-3 py-2 rounded-md bg-gradient-to-r from-gray-200 to-gray-300 text-gray-700 shadow hover:shadow-md hover:from-gray-300 hover:to-gray-400 transition-all duration-200" @click="clear">초기화</button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from "vue";
import { useSummaryVideoStore } from '@/stores/summaryVideoStore';
import { useSettingStore } from '@/stores/settingStore';
import { marked } from 'marked';
import Setting from '@/pages/Setting.vue';
import settingIcon from '@/assets/icons/setting.png';

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
// API 서버 URL을 동적으로 구성 (현재 페이지의 origin 기반)
const getApiBaseUrl = () => {
  // 개발 환경에서는 localhost:8001, 프로덕션에서는 현재 origin 사용
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://localhost:8001';
  }
  // 다른 환경에서는 현재 origin의 포트를 8001로 변경
  return `${window.location.protocol}//${window.location.hostname}:8001`;
};
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

function closeSettingModal() { showSettingModal.value = false; }

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
    console.warn('Failed to restore File from URL', e);
  }
}

async function restoreAllMissingFiles() {
  const targets = videoFiles.value.filter(v => !(v.file instanceof File) && (v.displayUrl || v.originUrl));
  for (const v of targets) {
    await restoreMissingFile(v);
  }
}

// Pinia 스토어에서 동영상 목록을 불러와서 Summarize 메뉴의 로컬 배열에 복사
onMounted(() => {
  document.addEventListener('click', handleGlobalClick);
  
  // 샘플 동영상 경로 초기화
  sampleVideoPath.value = `${getApiBaseUrl()}/sample/sample.mp4`;
  
  // 샘플 동영상 재생 시작
  if (sampleVideoPath.value && sampleVideoRef.value) {
    nextTick(() => {
      const video = sampleVideoRef.value;
      if (video) {
        video.play().catch(err => {
          console.warn('샘플 동영상 자동 재생 실패:', err);
        });
      }
    });
  }
  
  if (Array.isArray(summaryVideoStore.videos) && summaryVideoStore.videos.length > 0) {
    // Summarize 전용 표시 URL을 분리하여 Video Storage 원본 URL(ObjectURL)과 독립
    videoFiles.value = summaryVideoStore.videos.map(v => {
      const hasFile = v.file instanceof File;
      const summaryObjectUrl = hasFile ? URL.createObjectURL(v.file) : null; // Summarize에서 새로 만든 URL
      return {
        id: v.id,
        name: v.name ?? v.title,
        originUrl: v.url || '', // Video Storage에서 넘어온 원본 URL (삭제 시 revoke 금지)
        displayUrl: summaryObjectUrl || v.url || '', // 렌더링에 사용할 URL
        summaryObjectUrl, // Summarize가 관리/해제할 URL (없으면 null)
        date: v.date ?? '',
        summary: v.summary ?? '',
        file: hasFile ? v.file : null
      };
    });
    selectedIndexes.value = videoFiles.value.map(v => v.id);
    zoomedIndex.value = videoFiles.value.length > 0 ? 0 : null;
    // 초기 로딩 후 File 객체가 null인 항목 복원 시도 (세션 재진입, localStorage 경유 케스)
    restoreAllMissingFiles();
  }
});

// Summarize 페이지에서 벗어날 때 영상 URL 및 스토어 정리 (다시 들어왔을 때 이전 영상이 남지 않도록)
onUnmounted(() => {
  document.removeEventListener('click', handleGlobalClick);
  // Summarize에서 만든 전용 ObjectURL만 해제 (원본은 유지)
  videoFiles.value.forEach(v => {
    if (v.summaryObjectUrl) {
      try { URL.revokeObjectURL(v.summaryObjectUrl); } catch (_) { }
    }
  });
  summaryVideoStore.clearVideos();
  videoFiles.value = [];
  selectedIndexes.value = [];
  zoomedIndex.value = null;
});

// watch 제거: 매 변경마다 새 ObjectURL 생성되어 누수 가능성 감소

function onDragOver(e) {
  isDragging.value = true;
}
function onDragLeave(e) {
  isDragging.value = false;
}
function onDrop(e) {
  isDragging.value = false;
  const files = e.dataTransfer.files;
  if (files && files.length > 0) {
    const file = files[0];
    if (file.type.startsWith('video/')) {
      const summaryObjectUrl = URL.createObjectURL(file);
      videoFiles.value.push({
        id: Date.now() + Math.random(),
        name: file.name,
        originUrl: '', // 드롭 업로드는 Video Storage와 무관한 직접 업로드
        displayUrl: summaryObjectUrl,
        summaryObjectUrl,
        date: new Date().toISOString().slice(0, 10),
        summary: '',
        file
      });
    }
  }
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
  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    video,
    index: idx
  };
}

function handleGlobalClick() {
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

function contextDelete() {
  const { video } = contextMenu.value;
  closeContextMenu();
  if (!video) return;
  if (!selectedIndexes.value.includes(video.id) || selectedIndexes.value.length < 2) {
    selectedIndexes.value = [video.id];
  }
  if (selectedIndexes.value.length === 0) return;
  batchRemoveSelectedVideos();
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

function onUpload(e) {
  const files = Array.from(e.target.files ?? []);
  if (!files.length) return;

  const newVideos = files
    .filter(file => {
      if (!file.type.startsWith('video/')) {
        alert('동영상 파일만 업로드할 수 있습니다.');
        return false;
      }
      return true;
    })
    .map(file => {
      const summaryObjectUrl = URL.createObjectURL(file);
      return {
        id: Date.now() + Math.random(),
        name: file.name,
        originUrl: '',
        displayUrl: summaryObjectUrl,
        summaryObjectUrl,
        date: new Date().toISOString().slice(0, 10),
        summary: "",
        file
      };
    });
  videoFiles.value.unshift(...newVideos);
  // input[type=file] value 초기화 (동일 파일 재업로드 가능)
  if (fileInputRef.value) fileInputRef.value.value = '';
  if (videoFiles.value.length > 0 && selectedIndexes.value.length === 0) {
    selectedIndexes.value = videoFiles.value.map(v => v.id);
  }
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

  const VSS_API_URL = 'http://localhost:8001/vss-summarize';

  // 순차 처리 대상: 선택된 것이 있으면 선택 영상들, 없으면 전체
  const targetVideos = (selectedIndexes.value.length > 0)
    ? videoFiles.value.filter(v => selectedIndexes.value.includes(v.id))
    : [...videoFiles.value];

  if (targetVideos.length === 0) {
    alert('요약할 동영상이 없습니다.');
    return;
  }

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

  for (let idx = 0; idx < targetVideos.length; idx++) {
    const videoObj = targetVideos[idx];
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
    addChatMessage({
      id: loadingId,
      role: 'system',
      content: `⏳ [${idx + 1}/${targetVideos.length}] '${videoObj.name}' 요약 요청 중...`
    });
    const startTime = Date.now();

    const formData = new FormData();
    formData.append('file', videoObj.file);
    formData.append('prompt', prompt.value ?? '');
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

    // 경과 시간 추적기 설정
    const intervalId = setInterval(() => {
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
      const loadingIdx = chatMessages.value.findIndex(m => m.id === loadingId);
      if (loadingIdx !== -1) {
        chatMessages.value[loadingIdx].content = `⏳ [${idx + 1}/${targetVideos.length}] '${videoObj.name}' 요약 요청 중... (경과 시간: ${elapsed}s)`;
      }
    }, 10); // Update every 10ms for finer precision

    try {
      const res = await fetch(VSS_API_URL, { method: 'POST', body: formData });
      clearInterval(intervalId); // 요청 완료 시 타이머 정리
      const endTime = Date.now();
      const elapsed = ((endTime - startTime) / 1000).toFixed(2);
      if (!res.ok) {
        let errText = await res.text();
        const errHtml = `❌ [${idx + 1}/${targetVideos.length}] '${videoObj.name}' 실패 (HTTP ${res.status})<br><code>${errText}</code><br><div class='text-xs text-gray-500'>시간: ${elapsed}s`;
        // 로딩 메시지 제거
        const loadingIdx = chatMessages.value.findIndex(m => m.id === loadingId);
        if (loadingIdx !== -1) chatMessages.value.splice(loadingIdx, 1);
        addChatMessage({ id: Date.now() + Math.random(), role: 'system', content: errHtml });
        console.error('Summarization error response:', errText);
        continue;
      }
      const data = await res.json();
      const serverVideoId = data.video_id;
      summarizedVideoMap.value[videoObj.id] = serverVideoId;
      summarizedVideoId.value = serverVideoId; // 마지막 성공값 유지
      const markedsummary = marked.parse(data.summary || '');
      const summaryHtml = `<div class='font-semibold'>✅ [${idx + 1}/${targetVideos.length}] '${videoObj.name}' 요약 완료</div><br>${markedsummary}<br><div class='text-xs text-gray-500'>시간: ${elapsed}s | 서버 ID: ${serverVideoId}</div>`;
      response.value = summaryHtml; // 마지막 결과 저장용
      // 로딩 메시지 제거
      const loadingIdx = chatMessages.value.findIndex(m => m.id === loadingId);
      if (loadingIdx !== -1) chatMessages.value.splice(loadingIdx, 1);
      addChatMessage({ id: Date.now() + Math.random(), role: 'assistant', content: summaryHtml });
    } catch (e) {
      const endTime = Date.now();
      const elapsed = ((endTime - startTime) / 1000).toFixed(2);
      const errHtml = `❌ [${idx + 1}/${targetVideos.length}] '${videoObj.name}' 네트워크 오류: ${(e && e.message) || 'unknown'}<br><div class='text-xs text-gray-500'>시간: ${elapsed}s</div>`;
      const loadingIdx = chatMessages.value.findIndex(m => m.id === loadingId);
      if (loadingIdx !== -1) chatMessages.value.splice(loadingIdx, 1);
      addChatMessage({ id: Date.now() + Math.random(), role: 'system', content: errHtml });
      console.error('Summarization request failed:', e);
    }
  }

  // 전체 완료 메시지
  addChatMessage({
    id: Date.now() + Math.random(),
    role: 'system',
    content: `✅ 모든 요약 처리 완료 (${Object.keys(summarizedVideoMap.value).length}개 성공). 질의 시 선택된 영상의 서버 요약을 우선 사용합니다.`
  });
}

// 동영상이 1개일 때 삭제
function removeSingleVideo() {
  if (videoFiles.value.length === 1) {
    const target = videoFiles.value[0];
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


function batchRemoveSelectedVideos() {
  videoFiles.value
    .filter(v => selectedIndexes.value.includes(v.id))
    .forEach(v => {
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
  const VSS_API_URL = 'http://localhost:8001/vss-query';
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
      return;
    }
    formData.append('file', videoObj.file);
  }
  formData.append('query', ask_prompt.value ?? '');
  formData.append('chunk_size', safeNum(settingStore.chunk, 10));
  formData.append('top_k', safeNum(settingStore.topk, 1));
  formData.append('top_p', safeNum(settingStore.topp, 1.0));
  formData.append('temperature', safeNum(settingStore.temp, 1.0));
  formData.append('max_new_tokens', safeNum(settingStore.maxTokens, 512));
  formData.append('seed', safeNum(settingStore.seed, 1));

  // 사용자가 입력한 질문을 채팅창에 추가
  addChatMessage({ id: Date.now() + Math.random(), role: 'user', content: q });

  const res = await fetch(VSS_API_URL, { method: 'POST', body: formData });
  if (!res.ok) {
    alert(`질의 요청 실패 (HTTP ${res.status})`);
    return;
  }
  const data = await res.json();
  const markedanswer = marked.parse(data.summary || '');
  const answerHtml = `<div class='font-semibold'>✅ Query Answered</div><br>${markedanswer}`;
  addChatMessage({ id: Date.now() + Math.random(), role: 'assistant', content: answerHtml });

}

function clear() {
  prompt.value = "";
  response.value = "";
  chatMessages.value = [];
  scrollChatToBottom();
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

function saveResult() {
  // 결과 저장 로직 (필요시 구현)
  console.log('Save result:', response.value);
}
</script>

<style scoped>
.chat-row {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  animation: fadeIn 0.25s ease;
}
.chat-row.from-user { justify-content: flex-end; }

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
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.avatar-user { background: #3b82f6; color: #fff; }
.avatar-assistant { background: #10b981; color: #fff; }
.avatar-system { background: #6b7280; color: #fff; }

.chat-bubble {
  max-width: 70%;
  background: #ffffff;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  position: relative;
  box-shadow: 0 2px 6px rgba(0,0,0,0.08);
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.chat-bubble.assistant { background: #f8fafc; }
.chat-bubble.user { background: #eef6ff; }
.chat-bubble.system { background: #f3f4f6; font-size: 13px; }

.chat-bubble :deep(code) { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; }
.chat-bubble :deep(pre) {
  background: #1e293b;
  color: #f8fafc;
  padding: 10px 12px;
  border-radius: 8px;
  overflow: auto;
  font-size: 13px;
}
.chat-bubble :deep(pre code) { background: transparent; padding: 0; }

.chat-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
  color: #6b7280;
}
.chat-meta .time { user-select: none; }

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
.copy-btn:hover { background: #e5e7eb; }

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

.brightness-75 { filter: brightness(75%); transition: filter 0.3s ease; }
.chat-window { backdrop-filter: blur(2px); }
.chat-row { transition: transform 0.3s ease, opacity 0.3s ease; }
.chat-row:hover { transform: translateY(-2px); }
.chat-bubble { transition: box-shadow 0.3s ease, background 0.3s ease; }
.chat-bubble.assistant:hover { box-shadow: 0 4px 12px rgba(16,185,129,0.25); }
.chat-bubble.user:hover { box-shadow: 0 4px 12px rgba(59,130,246,0.25); }
.chat-bubble.system:hover { box-shadow: 0 4px 12px rgba(107,114,128,0.25); }
.transition-all { transition: opacity 0.3s ease, transform 0.3s ease; }
</style>

