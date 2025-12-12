<template>
  <!-- 메뉴 틀 -->
  <div id="video_list" class="w-full h-full bg-gradient-to-br from-gray-200 to-gray-300 via-gray-100 p-10">
    <div class="w-full h-full bg-gray-50 rounded-2xl shadow-inner p-10">
      <!-- 헤더 -->
      <header id="header" class="flex items-center justify-between px-1 pb-3 border-b border-gray-800/70">
        <!-- 좌측: 타이틀 / 설명 -->
        <div class="flex flex-col gap-1">
          <div
            class="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-400/40 w-fit">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span class="text-[11px] font-semibold tracking-wide text-emerald-600 uppercase">
              Video Search Workspace
            </span>
          </div>
          <p class="text-xs md:text-sm text-black mt-1">
            업로드한 여러 동영상에서 원하는 장면을 검색하고,
            <span class="hidden md:inline">오른쪽 패널에서 검색 결과 클립을 한눈에 확인할 수 있습니다.</span>
          </p>
        </div>

        <!-- 우측: 전체 선택 + 업로드 버튼 -->
        <div class="flex items-center gap-3">
          <!-- Select All (데스크톱용 텍스트 버튼) -->
          <button
            class="hidden md:inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-slate-500/60 text-[13px] text-slate-100 bg-slate-900/70 hover:bg-slate-800/80 hover:border-emerald-400/70 hover:text-emerald-50 shadow-sm transition-all duration-200 disabled:opacity-40 disabled:cursor-default"
            :disabled="items.length === 0" @click="allselect()">
            <span
              class="inline-flex items-center justify-center w-5 h-5 rounded-md bg-slate-950/80 text-[11px] font-semibold text-slate-50">
              {{ selectedIds.length === items.length && items.length > 0 ? '✓' : ' ' }}
            </span>
            <span class="font-medium">
              {{ selectedIds.length === items.length && items.length > 0 ? 'Clear Selection' : 'Select All' }}
            </span>
          </button>

          <!-- Select All (모바일 아이콘 버튼) -->
          <button
            class="md:hidden flex items-center justify-center w-9 h-9 rounded-2xl border border-slate-500/60 bg-slate-900/70 text-slate-100 hover:bg-slate-800/90 hover:border-emerald-400/70 transition-all duration-200 disabled:opacity-40 disabled:cursor-default"
            :disabled="items.length === 0" @click="allselect()" title="Select All">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
          </button>

          <!-- 업로드 버튼 -->
          <div class="flex items-center h-12">
            <label
              class="inline-flex items-center gap-2 rounded-2xl bg-emerald-500/90 hover:bg-emerald-400 text-white px-5 py-2.5 shadow-lg shadow-emerald-500/30 cursor-pointer transform transition-all duration-200 hover:scale-[1.03] active:scale-[0.97]">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M12 12v7m0-7l-3 3m3-3l3 3"></path>
              </svg>
              <span class="font-medium text-sm">Upload Video</span>
              <input type="file" accept="video/*" multiple class="hidden" @change="handleUpload" />
            </label>
          </div>
        </div>
      </header>
        <!-- 동영상 출력 영역 -->
        <div 
          class="relative w-full h-[90%] border border-slate-200/80 rounded-2xl overflow-y-auto shadow-inner mt-4 transition-all duration-300"
          :class="isDragOverUpload ? 'bg-blue-100 border-blue-400 ring-2 ring-blue-300' : 'bg-gray-50'"
          @dragover.prevent="onDragOverUpload"
          @dragleave.prevent="onDragLeaveUpload"
          @drop.prevent="onDropUpload">
          <div v-if="items.length === 0" class="flex items-center justify-center h-full">
            <div
              class="w-[30%] h-[9%] inline-flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 text-gray-500 text-center text-[24px] border border-gray-200 rounded-2xl shadow-sm backdrop-blur-sm transition-all duration-300"
              :class="isDragOverUpload ? 'bg-blue-50 border-blue-300 text-blue-600' : ''">
              <p v-if="!isDragOverUpload" class="font-light">Please upload a video</p>
              <p v-else class="font-bold">여기에 파일을 놓으세요</p>
            </div>
          </div>

          <!-- 드래그 & 드롭 오버레이 (동영상이 있을 때) -->
          <div 
            v-if="isDragOverUpload && items.length > 0"
            class="absolute inset-0 z-50 flex items-center justify-center bg-blue-500/20 backdrop-blur-sm border-4 border-dashed border-blue-400 rounded-2xl pointer-events-none">
            <div class="bg-white/90 rounded-2xl px-8 py-6 shadow-xl">
              <p class="text-2xl font-bold text-blue-600 text-center">여기에 파일을 놓으세요</p>
            </div>
          </div>

          <!-- 동영상 출력 그리드(행열 구조) -->
          <div 
            class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6 p-6 overflow-y-auto transition-opacity duration-300"
            :class="{ 'opacity-50': isDragOverUpload && items.length > 0 }">
            <div v-for="video in items" :key="video.id"
              class="flex flex-col items-center justify-center rounded-2xl shadow-md hover:shadow-xl cursor-pointer p-3 border border-gray-200 relative transform transition-all duration-300 hover:scale-105 hover:-translate-y-1 group"
              :class="{ 'ring-2 ring-blue-400 bg-blue-100': selectedIds.includes(video.id) }"
              @click="onCardClick(video.id, $event)" @contextmenu.prevent.stop="onVideoContextMenu(video, $event)">
              <div
                class="w-[100%] h-[100%] flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 rounded-xl mb-2 overflow-hidden relative group-hover:from-gray-200 group-hover:to-gray-300 transition-all duration-300"
                @mouseenter="hoveredVideoId = video.id" @mouseleave="hoveredVideoId = null">
                <video :ref="el => (videoRefs[video.id] = el)" v-if="video.displayUrl" :src="video.displayUrl"
                  class="object-cover rounded-xl transition-transform duration-300 group-hover:scale-105"
                  preload="metadata" @timeupdate="updateProgress(video.id, $event)"
                  @loadedmetadata="onVideoMetadataLoaded(video.id, $event)"></video>
                <span v-else class="text-gray-400 text-sm">No Thumbnail</span>
                <!-- 그리드: 재생 중이 아닐 때 어두워지는 오버레이 -->
                <div v-if="video.displayUrl" class="absolute inset-0 pointer-events-none transition-colors duration-300"
                  :class="playingVideoIds.includes(video.id) ? 'bg-transparent' : 'bg-black/20'"></div>
                <!-- 재생하지 않은 동영상의 영상 길이 표시 (우측 하단) -->
                <div v-if="video.displayUrl && !playingVideoIds.includes(video.id) && durationMap[video.id]"
                  class="absolute bottom-2 right-2 px-2 py-1 bg-black/70 backdrop-blur-sm text-white text-xs font-medium rounded pointer-events-none">
                  {{ formatTime(durationMap[video.id]) }}
                </div>
                <!-- 재생 버튼 -->
                <button @click.stop="togglePlay(video.id)" :class="{
                  'opacity-100 scale-100': hoveredVideoId === video.id || !playingVideoIds.includes(video.id),
                  'opacity-0 scale-90': hoveredVideoId !== video.id && playingVideoIds.includes(video.id),
                }"
                  class="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-black/60 to-black/40 backdrop-blur-sm text-white rounded-full w-14 h-14 m-auto transition-all duration-300 hover:scale-110 active:scale-95">
                  <!-- 재생 시작 아이콘 -->
                  <svg v-if="!playingVideoIds.includes(video.id)" xmlns="http://www.w3.org/2000/svg" fill="currentColor"
                    viewBox="0.4 -0.7 16 16" class="w-8 h-8">
                    <path
                      d="M6.271 4.055a.5.5 0 0 1 .759-.429l4.592 3.11a.5.5 0 0 1 0 .828l-4.592 3.11a.5.5 0 0 1-.759-.429V4.055z" />
                  </svg>

                  <!-- 재생 중단 아이콘 -->
                  <svg v-else xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0.4 -0.1 16 16"
                    class="w-8 h-8">
                    <path
                      d="M5.5 3.5A.5.5 0 0 1 6 3h1a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5H6a.5.5 0 0 1-.5-.5v-9zM9.5 3.5A.5.5 0 0 1 10 3h1a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-9z" />
                  </svg>
                </button>

                <!-- 재생 프로그레스 바 (재생 중일 때만 표시, 마우스 hover 시 표시) -->
                <div
                  v-if="playingVideoIds.includes(video.id)"
                  class="absolute bottom-0 left-0 right-0 p-2 bg-black/30 backdrop-blur-sm rounded-b-xl transition-all duration-300 pointer-events-none"
                  :class="{
                    'opacity-100 translate-y-0': hoveredVideoId === video.id || !playingVideoIds.includes(video.id),
                    'opacity-0 translate-y-full': hoveredVideoId !== video.id && playingVideoIds.includes(video.id)
                  }">
                  <div class="flex flex-col gap-1">
                    <!-- 재생 프로그레스 바 백그라운드 -->
                    <div
                      class="relative w-full h-2 bg-gray-300/70 rounded-full cursor-pointer pointer-events-auto overflow-visible"
                      :class="{ 'dragging': isDragging && draggedVideoId === video.id }"
                      :ref="el => { if (el) progressBarRefs[video.id] = el }"
                      @click.stop="seekVideo(video.id, $event)">
                      <!-- 재생 프로그레스 바 진행 상태 -->
                      <div
                        class="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full shadow-sm overflow-hidden"
                        :class="{ 'transition-all duration-300': !(isDragging && draggedVideoId === video.id) }"
                        :style="{ width: `${video.progress || 0}%` }"></div>
                      <!-- 재생 프로그레스 바 핸들 -->
                      <div
                        class="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white rounded-full border border-blue-500 cursor-pointer shadow hover:shadow-md hover:scale-110 transition-all pointer-events-auto z-10"
                        :class="{ 'transition-none': isDragging && draggedVideoId === video.id }"
                        :style="{ left: `calc(${video.progress || 0}% - 8px)` }"
                        @mousedown="startDragging(video.id, $event)" @click.stop></div>
                    </div>

                    <!-- 재생 시간 표시 -->
                    <div
                      class="flex justify-between text-[10px] font-medium text-gray-200 tracking-wide px-1 pointer-events-auto">
                      <span>{{ formatTime(currentTimeMap[video.id] || 0) }}</span>
                      <span>{{ formatTime(durationMap[video.id] || 0) }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <!-- 동영상 타이틀 및 정보 -->
              <div class="ml-4 w-full text-left">
                <div v-if="video.title" class="text-sm font-medium text-gray-800 truncate">
                  {{ video.title }}
                </div>
                <!-- 영상 정보: 길이, 해상도, 용량 (가로 나열) -->
                <div class="mt-1 text-xs text-gray-500 flex flex-wrap items-center gap-x-2 gap-y-0.5">
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
          
          <!-- 우측 하단 원형 버튼 -->
          <button
            class="absolute bottom-6 right-6 w-14 h-14 rounded-full bg-emerald-500 hover:bg-emerald-600 text-white shadow-lg hover:shadow-xl flex items-center justify-center transition-all duration-300 transform hover:scale-110 active:scale-95 z-50"
            @click="handleAddButtonClick">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" viewBox="0 0 24 24" class="w-6 h-6">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
          </button>
        </div>
        <!-- 확대 모달 팝업 - Teleport로 body에 렌더링 -->
        <Teleport to="body">
          <Transition name="modal">
            <div v-if="isZoomed" class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 p-4"
              @click.self="unzoomVideo">
              <div class="bg-white rounded-xl shadow-2xl w-full max-w-4xl relative" @click.stop>
                <!-- 비디오 영역 (확대 전용 - 하얀 프레임 + 하단 진행 바/타이틀) -->
                <div class="relative w-full p-4 bg-white rounded-2xl shadow-inner flex flex-col">
                  <!-- 닫기 버튼: 프레임 우측 상단 -->
                  <button @click="unzoomVideo"
                    class="ml-auto mb-3 z-10 w-6 h-6 flex items-center justify-center bg-black/50 hover:bg-black/70 rounded-full text-white transition-all duration-200">
                    <!-- 닫기 아이콘 -->
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12">
                      </path>
                    </svg>
                  </button>


                  <div
                    class="relative w-full aspect-video flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 rounded-xl overflow-hidden group zoom-group"
                    @mouseenter="hoveredVideoId = zoomedVideo?.id" @mouseleave="hoveredVideoId = null">
                    <video v-if="zoomedVideo" ref="zoomVideoRef" :src="zoomedVideo.displayUrl"
                      class="object-cover w-full h-full" preload="metadata" crossorigin="anonymous"
                      @timeupdate="onZoomTimeUpdate($event)"
                      @error="(e) => console.warn('zoom video error', e, zoomedVideo && zoomedVideo.displayUrl)"></video>
                    <div v-if="zoomedVideo" class="absolute inset-0 pointer-events-none transition-colors duration-300"
                      :class="zoomPlaying ? 'bg-transparent' : 'bg-black/30'"></div>
                    <button v-if="zoomedVideo" @click.stop="togglePlay(zoomedVideo.id)" :class="[
                      !zoomPlaying
                        ? 'opacity-100 scale-100 pointer-events-auto'
                        : (hoveredVideoId === zoomedVideo.id
                          ? 'opacity-100 scale-100 pointer-events-auto'
                          : 'opacity-0 scale-90 pointer-events-none'),
                      'absolute inset-0 flex items-center justify-center bg-gradient-to-br from-black/60 to-black/40 backdrop-blur-sm text-white rounded-full w-16 h-16 m-auto transition-all duration-300 hover:scale-110 active:scale-95 z-20'
                    ]">
                      <svg v-if="!zoomPlaying" xmlns="http://www.w3.org/2000/svg" fill="currentColor"
                        viewBox="0.4 -0.7 16 16" class="w-10 h-10">
                        <path
                          d="M6.271 4.055a.5.5 0 0 1 .759-.429l4.592 3.11a.5.5 0 0 1 0 .828l-4.592 3.11a.5.5 0 0 1-.759-.429V4.055z" />
                      </svg>
                      <svg v-else xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0.4 -0.1 16 16"
                        class="w-10 h-10">
                        <path
                          d="M5.5 3.5A.5.5 0 0 1 6 3h1a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5H6a.5.5 0 0 1-.5-.5v-9zM9.5 3.5A.5.5 0 0 1 10 3h1a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-9z" />
                      </svg>
                    </button>
                  </div>
                  <!-- 하단 진행 바 + 타이틀 영역 -->
                  <div v-if="zoomedVideo" class="mt-4 w-full flex flex-col gap-2">
                    <div ref="zoomProgressBarRef"
                      class="relative w-full h-3 bg-gray-200 rounded-full cursor-pointer zoom-progress-bar overflow-visible"
                      :class="{ 'dragging': isDragging && draggedVideoId === zoomedVideo.id }"
                      @click.stop="seekVideo(zoomedVideo.id, $event)">
                      <div
                        class="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full shadow-sm overflow-hidden"
                        :class="{ 'transition-all duration-300': !(isDragging && draggedVideoId === zoomedVideo.id) }"
                        :style="{ width: `${zoomProgress}%` }"></div>
                      <div
                        class="absolute top-1/2 h-5 w-5 bg-white rounded-full shadow-lg transform -translate-x-1/2 -translate-y-1/2 transition-all duration-200 border-2 border-blue-500 z-[20] cursor-grab active:cursor-grabbing"
                        :class="{ 'transition-none': isDragging && draggedVideoId === zoomedVideo.id }"
                        :style="{ left: `${zoomProgress}%` }" @mousedown="startDragging(zoomedVideo.id, $event)"></div>
                    </div>
                    <div class="flex items-center justify-between text-xs font-medium text-gray-600">
                      <div class="flex items-center gap-2">
                        <span v-if="zoomedVideo.title"
                          class="text-sm font-semibold text-gray-800 truncate max-w-[50vw]">{{ zoomedVideo.title
                          }}</span>
                      </div>
                      <div class="flex items-center gap-3 text-gray-500">
                        <span>{{ formatTime(zoomCurrentTime) }}</span>
                        <span>/</span>
                        <span>{{ formatTime(zoomDuration) }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Transition>
        </Teleport>
        <!-- 우클릭 컨텍스트 메뉴 (Teleport로 body에 렌더링) -->
        <Teleport to="body">
          <div v-if="contextMenu.visible" class="fixed z-[200]"
            :style="{ left: `${contextMenu.x}px`, top: `${contextMenu.y}px` }" @click.stop>
            <div class="bg-white rounded-lg shadow-xl border border-gray-100 overflow-hidden w-[200px]">
              <button v-if="selectedIds.length < 2" class="w-full text-left px-4 py-3 hover:bg-gray-50"
                @click.stop="contextZoom">확대</button>
              <button class="w-full text-left px-4 py-3 hover:bg-gray-50" @click.stop="contextSummary">요약 진행</button>
              <button class="w-full text-left px-4 py-3 hover:bg-gray-50" @click.stop="contextSearch" :disabled="selectedIds.length === 0">검색</button>
              <button class="w-full text-left px-4 py-3 hover:bg-gray-50" @click.stop="contextRemoveSummary" :disabled="selectedIds.length === 0">요약 결과 제거</button>
              <div class="h-px bg-gray-100"></div>
              <button class="w-full text-left px-4 py-3 text-red-600 hover:bg-gray-50" @click.stop="contextDelete">{{
                selectedIds.length > 1 ? `선택된 항목 삭제 (${selectedIds.length})` : '삭제' }}</button>
            </div>
          </div>
        </Teleport>

        <!-- 중앙 팝업창 -->
        <Transition name="modal">
          <div v-if="showDeletePopup"
            class="fixed inset-0 flex items-center justify-center z-[100] bg-black/50 backdrop-blur-sm rounded-2xl">
            <div
              class="bg-white rounded-2xl shadow-2xl p-8 min-w-[350px] max-w-[90vw] relative transform transition-all duration-300">
              <div class="text-lg font-semibold mb-6 text-center text-gray-800">
                <p class="mb-2">{{ selectedIds.length }}개의 동영상이 삭제됩니다.</p>
                <p class="text-sm font-normal text-gray-600">진행하시겠습니까?</p>
              </div>
              <div class="flex justify-end gap-3 mt-8">
                <button
                  class="px-6 py-2.5 rounded-xl bg-slate-700 text-white hover:bg-slate-800 transition-all duration-300 transform hover:scale-105 active:scale-95 font-medium shadow-sm"
                  @click="confirmDelete">delete</button>
                <button
                  class="px-6 py-2.5 rounded-xl bg-gray-200 text-gray-700 hover:bg-gray-300 transition-all duration-300 transform hover:scale-105 active:scale-95 font-medium shadow-sm"
                  @click="showDeletePopup = false">cancel</button>
              </div>
            </div>
          </div>
        </Transition>

        <!-- Search 사이드 메뉴 (전체 인터페이스 기준, Teleport 사용) -->
        <Teleport to="body">
          <!-- 배경 오버레이 -->
          <Transition name="overlay">
            <div v-if="showSearchSidebar" class="fixed inset-0 z-[150] bg-black/40 backdrop-blur-sm"
              @click="closeSearchSidebar">
            </div>
          </Transition>

          <!-- 사이드바 패널 - ChatGPT 스타일 -->
          <Transition name="sidebar">
            <div v-if="showSearchSidebar"
              class="fixed top-0 right-0 z-[151] bg-white w-[70%] h-full shadow-2xl flex flex-col" @click.stop>
              <!-- 사이드바 헤더 -->
              <div class="flex flex-col border-b border-gray-200 bg-gradient-to-r from-white to-gray-50">
                <div class="flex items-center justify-between p-4">
                  <div class="flex items-center gap-3">
                    <div
                      class="w-8 h-8 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center">
                      <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v6m3-3H7"></path>
                      </svg>
                    </div>
                    <h2 class="text-lg font-semibold text-gray-800">Video Search</h2>
                  </div>
                  <div class="flex items-center gap-2">
                    <!-- 신규 채팅창 추가 버튼 -->
                    <button @click="handleNewChatButtonClick"
                      class="relative p-2 hover:bg-gray-100 rounded-full transition-colors group" title="신규 채팅창 추가">
                      <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                      </svg>
                      <!-- 툴팍 -->
                      <div
                        class="absolute top-full left-1/2 transform -translate-x-1/2 mt-2 px-2 py-1 bg-gray-800 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                        신규 채팅창 추가
                        <div
                          class="absolute bottom-full left-1/2 transform -translate-x-1/2 -mb-1 w-0 h-0 border-l-4 border-r-4 border-b-4 border-transparent border-b-gray-800">
                        </div>
                      </div>
                    </button>
                    <button @click="closeSearchSidebar" class="p-2 hover:bg-gray-100 rounded-full transition-colors">
                      <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12">
                        </path>
                      </svg>
                    </button>
                  </div>
                </div>
                <!-- 채팅창 탭 -->
                <div v-if="chatSessions.length > 0" class="flex gap-2 px-4 pb-2 overflow-x-auto">
                  <div v-for="(chat, index) in chatSessions" :key="chat.id"
                    @click="editingChatIndex !== index && switchChat(index)" :class="{
                      'bg-gradient-to-r from-green-500 to-green-600 text-white shadow-md': currentChatIndex === index,
                      'bg-gray-100 text-gray-700 hover:bg-gray-200': currentChatIndex !== index
                    }"
                    class="px-3 py-1.5 rounded-t-xl text-sm font-medium transition-all duration-300 whitespace-nowrap flex items-center gap-2 cursor-pointer transform hover:scale-105">
                    <!-- 편집 모드 -->
                    <input v-if="editingChatIndex === index" v-model="editingChatName" @blur="saveChatName(index)"
                      @keydown.enter="saveChatName(index)" @keydown.esc="cancelEditChatName"
                      class="bg-transparent border-b border-current outline-none min-w-[60px] max-w-[120px] text-sm"
                      ref="chatNameInput" />
                    <!-- 일반 모드 -->
                    <span v-else @dblclick.stop="startEditChatName(index)" class="select-none">
                      {{ chat.name || `채팅 ${index + 1}` }}
                    </span>
                    <button v-if="chatSessions.length > 1 && editingChatIndex !== index" @click.stop="deleteChat(index)"
                      class="hover:bg-black hover:bg-opacity-20 rounded-full p-0.5">
                      <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12">
                        </path>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>

              <!-- 채팅 메시지 영역 -->
              <div ref="chatContainer" class="flex-1 overflow-y-auto bg-gray-50 p-4 space-y-4">
                <!-- 채팅 메시지들 -->
                <div v-for="(message, index) in currentChatMessages" :key="index" class="flex items-start gap-3"
                  :class="{ 'flex-row-reverse': message.role === 'user' }">
                  <!-- AI 메시지 -->
                  <div v-if="message.role === 'assistant'"
                    class="w-8 h-8 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center flex-shrink-0 overflow-hidden relative">
                    <!-- 클립 썸네일 있을 경우 첫 번째 클립을 아바타로 표시 -->
                    <template v-if="message.clips && message.clips.length > 0">
                      <video :src="message.clips[0].url" class="w-full h-full object-cover" muted playsinline
                        @error="(e) => console.warn('avatar video error', e, message.clips[0].url)"
                        crossorigin="anonymous"></video>
                      <div v-if="message.clips.length > 1"
                        class="absolute bottom-0 right-0 bg-black/60 text-[10px] text-white px-1 rounded">
                        +{{ message.clips.length - 1 }}
                      </div>
                    </template>
                    <template v-else>
                      <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v6m3-3H7"></path>
                      </svg>
                    </template>
                  </div>
                  <!-- 사용자 메시지 -->
                  <div v-else class="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center flex-shrink-0">
                    <svg class="w-4 h-4 text-gray-600" fill="currentColor" viewBox="0 0 24 24">
                      <path
                        d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z">
                      </path>
                    </svg>
                  </div>

                  <div class="flex-1" :class="{ 'flex flex-col items-end': message.role === 'user' }">
                    <div :class="{
                      'bg-white rounded-2xl rounded-tl-sm px-4 py-3 shadow-md border border-gray-200': message.role === 'assistant',
                      'bg-gradient-to-r from-green-500 to-green-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-md': message.role === 'user'
                    }">
                      <p :class="{
                        'text-gray-800 text-sm leading-relaxed': message.role === 'assistant',
                        'text-white text-sm leading-relaxed': message.role === 'user'
                      }" v-html="message.content"></p>
                      <!-- 초기 메시지의 선택된 동영상 목록 -->
                      <div v-if="message.isInitial && message.selectedVideos && message.selectedVideos.length > 0"
                        class="mt-3 space-y-2">
                        <p class="text-xs text-gray-500 font-medium mb-2">선택된 동영상:</p>
                        <div v-for="video in message.selectedVideos" :key="video.id"
                          class="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                          <video :src="video.displayUrl" class="w-32 h-20 object-cover rounded flex-shrink-0"></video>
                          <div class="flex-1 min-w-0">
                            <p class="text-sm font-medium text-gray-800 truncate">{{ video.title }}</p>
                            <p class="text-xs text-gray-500 mt-1">{{ video.date }}</p>
                          </div>
                        </div>
                      </div>
                      <!-- 검색 결과(클립) 표시 -->
                      <div v-if="message.clips && message.clips.length > 0" class="mt-3 space-y-2">
                        <p
                          :class="message.role === 'assistant' ? 'text-xs text-gray-500 font-medium mb-2' : 'text-xs text-green-100 font-medium mb-2'">
                          검색 결과 ({{ message.clips.length }}개):
                        </p>
                        <div v-for="clip in message.clips" :key="clip.id"
                          :class="message.role === 'assistant' ? 'flex items-center gap-3 p-3 bg-gray-50 rounded-xl transition-all duration-200 hover:bg-gray-100' : 'flex items-center gap-3 p-3 bg-green-600/80 rounded-xl transition-all duration-200 hover:bg-green-600'">
                          <video :src="clip.url" class="w-32 h-20 object-cover rounded cursor-pointer flex-shrink-0" preload="metadata"
                            @click.stop="zoomClip(clip)"
                            @error="(e) => console.warn('clip thumbnail error', e, clip.url)"
                            crossorigin="anonymous"></video>
                          <div class="flex-1 min-w-0">
                            <p
                              :class="message.role === 'assistant' ? 'text-sm font-medium text-gray-800 truncate' : 'text-sm font-medium text-white truncate'">
                              {{ clip.title }}</p>
                            <p
                              :class="message.role === 'assistant' ? 'text-xs text-gray-500 mt-1' : 'text-xs text-green-100 mt-1'">
                              <span v-if="clip.start_time !== undefined && clip.end_time !== undefined">
                                {{ formatTime(clip.start_time) }} - {{ formatTime(clip.end_time) }}
                              </span>
                              <span v-else>
                                {{ clip.sourceVideo || clip.date }}
                              </span>
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                    <p
                      :class="message.role === 'assistant' ? 'text-xs text-gray-400 mt-1 ml-2' : 'text-xs text-gray-400 mt-1 mr-2'">
                      {{ message.timestamp }}</p>
                  </div>
                </div>

                <!-- 로딩 인디케이터 -->
                <div v-if="isSearching" class="flex items-start gap-3">
                  <div
                    class="w-8 h-8 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center flex-shrink-0">
                    <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v6m3-3H7"></path>
                    </svg>
                  </div>
                  <div class="flex-1">
                    <div class="bg-white rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm border border-gray-200">
                      <div class="flex gap-1">
                        <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0s"></div>
                        <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s">
                        </div>
                        <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.4s">
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 입력 영역 (하단 고정) -->
              <div class="border-t border-gray-200 bg-white p-4">
                <div class="flex items-end gap-2">
                  <div class="flex-1 relative">
                    <textarea v-model="searchInput" @keydown.enter.exact.prevent="handleSearch"
                      @keydown.shift.enter.exact="searchInput += '\n'" placeholder="검색할 장면에 대한 정보를 입력해주세요..." rows="1"
                      class="w-full px-4 py-3 pr-12 border border-gray-300 rounded-2xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none max-h-32 overflow-y-auto text-sm"
                      style="min-height: 44px;"></textarea>
                    <button @click="handleSearch" :disabled="!searchInput.trim() || isSearching"
                      class="absolute right-2 bottom-2 p-2 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-xl hover:from-green-600 hover:to-green-700 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-110 active:scale-95 shadow-md">
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8">
                        </path>
                      </svg>
                    </button>
                  </div>
                </div>
                <p class="text-xs text-gray-400 mt-2 text-center">Enter를 눌러 검색하거나 Shift+Enter로 줄바꿈</p>
              </div>
            </div>
          </Transition>
        </Teleport>

        <!-- 업로드 진행률 모달 -->
        <Teleport to="body">
          <div v-if="showUploadModal" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div class="bg-white rounded-2xl shadow-2xl max-w-2xl w-full mx-4 p-6">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold text-gray-800">동영상 업로드 중...</h3>
                <button @click="closeUploadModal" class="text-gray-400 hover:text-gray-600 transition-colors">
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div class="space-y-4 max-h-[60vh] overflow-y-auto">
                <div v-for="(upload, index) in uploadProgress" :key="upload.id" class="border border-gray-200 rounded-lg p-4">
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-medium text-gray-700 truncate flex-1 mr-2">{{ upload.fileName }}</span>
                    <span class="text-sm text-gray-500 whitespace-nowrap">{{ upload.progress }}%</span>
                  </div>
                  <div class="w-full bg-gray-200 rounded-full h-2.5 mb-2">
                    <div 
                      class="bg-gradient-to-r from-emerald-500 to-emerald-600 h-2.5 rounded-full transition-all duration-300"
                      :style="{ width: `${upload.progress}%` }"
                    ></div>
                  </div>
                  <div class="flex items-center justify-between text-xs text-gray-500">
                    <span>{{ upload.status }}</span>
                    <span v-if="upload.uploaded > 0">{{ formatFileSize(upload.uploaded) }} / {{ formatFileSize(upload.total) }}</span>
                  </div>
                </div>
              </div>
              <div v-if="allUploadsComplete" class="mt-4 text-center">
                <button @click="closeUploadModal" class="px-6 py-2 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition-colors">
                  완료
                </button>
              </div>
            </div>
          </div>
        </Teleport>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onActivated, computed, nextTick, watch, onBeforeUnmount } from "vue";
import { useRouter } from 'vue-router';
import { useSummaryVideoStore } from '@/stores/summaryVideoStore';

const isZoomed = ref(false);
const zoomedVideo = ref(null);
const zoomVideoRef = ref(null);
const zoomProgressBarRef = ref(null);
const zoomPlaying = ref(false); // 확대 모달 재생 상태 (그리드와 분리)
const zoomProgress = ref(0);   // 확대 모달 진행률 (그리드와 분리)
const showSearchSidebar = ref(false);
const hoveredVideoId = ref(null);
const playingVideoIds = ref([]);
const showDeletePopup = ref(false);
const items = ref([]);
const selectedIds = ref([]);
const videoRefs = ref({});
const progressBarRefs = ref({}); // 비디오별 진행바 엘리먼트 참조
const isDragging = ref(false);
const draggedVideoId = ref(null);
let draggingBarEl = null; // 현재 드래그 중인 진행바 엘리먼트
const isDragOverUpload = ref(false); // 드래그 & 드롭 업로드 상태
const chatSessions = ref([]);
const currentChatIndex = ref(0);
const searchInput = ref('');
const isSearching = ref(false);
const chatContainer = ref(null);
const editingChatIndex = ref(null);
const editingChatName = ref('');
const chatNameInput = ref(null);
// 업로드 진행률 모달 상태
const showUploadModal = ref(false);
const uploadProgress = ref([]); // { id, fileName, progress, status, uploaded, total }

// 시간 표시용 맵 (Summary.vue 스타일 이식)
const currentTimeMap = ref({});
const durationMap = ref({});

// 확대 모달 시간 표시용
const zoomCurrentTime = ref(0);
const zoomDuration = ref(0);
// Context menu state for right-click on video cards
const contextMenu = ref({ visible: false, x: 0, y: 0, video: null });

function onVideoContextMenu(video, e) {
  // If the user already has multiple items selected, do not change selection
  if (selectedIds.value.length < 2) {
    if (!selectedIds.value.includes(video.id)) {
      selectedIds.value = [video.id];
    }
  }

  // 기본 좌표는 마우스 위치
  let x = e.clientX;
  let y = e.clientY;

  // 메뉴 크기 (너비 200px, 높이는 대략 200px 정도)
  const menuWidth = 200;
  const menuHeight = 200;

  // 화면 경계 확인 및 조정
  const windowWidth = window.innerWidth;
  const windowHeight = window.innerHeight;

  // 오른쪽 경계를 넘어가면 왼쪽으로 조정
  if (x + menuWidth > windowWidth) {
    x = windowWidth - menuWidth - 10; // 10px 여백
  }

  // 아래쪽 경계를 넘어가면 위로 조정
  if (y + menuHeight > windowHeight) {
    y = windowHeight - menuHeight - 10; // 10px 여백
  }

  // 왼쪽 경계 확인
  if (x < 10) {
    x = 10;
  }

  // 위쪽 경계 확인
  if (y < 10) {
    y = 10;
  }

  contextMenu.value = { visible: true, x, y, video };
}

function closeContextMenu() {
  contextMenu.value.visible = false;
  contextMenu.value.video = null;
}

function contextZoom() {
  if (!contextMenu.value.video) return;
  zoomVideo(contextMenu.value.video);
  closeContextMenu();
}

function contextSummary() {
  goToSummary();
  closeContextMenu();
}

function contextSearch() {
  if (selectedIds.value.length === 0) {
    return;
  }
  goToSearch();
  closeContextMenu();
}

function contextDelete() {
  if (!contextMenu.value.video) return;
  // If multiple items are already selected, delete those; otherwise delete the clicked one
  if (selectedIds.value.length < 2) {
    const id = contextMenu.value.video.id;
    selectedIds.value = [id];
  }
  closeContextMenu();
  showDeletePopup.value = true; // reuse existing delete confirmation flow
}

async function contextRemoveSummary() {
  if (selectedIds.value.length === 0) return;
  closeContextMenu();
  
  const userId = localStorage.getItem("vss_user_id");
  if (!userId) {
    alert('로그인이 필요합니다.');
    return;
  }
  
  // 선택된 동영상의 dbId 가져오기
  const videosToRemoveSummary = items.value
    .filter(video => selectedIds.value.includes(video.id))
    .map(video => video.dbId || video.id)
    .filter(id => id != null);
  
  if (videosToRemoveSummary.length === 0) {
    alert('요약 결과를 제거할 동영상을 찾을 수 없습니다.');
    return;
  }
  
  try {
    const response = await fetch('http://localhost:8001/summaries', {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        video_ids: videosToRemoveSummary,
        user_id: userId
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: '알 수 없는 오류' }));
      alert(`요약 결과 제거 실패: ${errorData.detail || '알 수 없는 오류'}`);
      return;
    }
    
    const data = await response.json();
    if (data.success) {
      alert(data.message || `${data.deleted_count || 0}개의 요약 결과가 제거되었습니다.`);
    } else if (data.deleted_count === 0) {
      alert('삭제할 요약 결과가 없습니다.');
    } else {
      alert('요약 결과 제거에 실패했습니다.');
    }
  } catch (error) {
    console.error('요약 결과 제거 중 오류:', error);
    alert(`요약 결과 제거 중 오류가 발생했습니다: ${error.message}`);
  }
}

function handleGlobalClick(e) {
  if (!contextMenu.value.visible) return;
  // close when clicking outside
  closeContextMenu();
}

onMounted(() => window.addEventListener('click', handleGlobalClick));
onBeforeUnmount(() => window.removeEventListener('click', handleGlobalClick));

function allselect() {
  if (selectedIds.value.length === items.value.length) {
    selectedIds.value = [];
  } else {
    selectedIds.value = items.value.map(v => v.id);
  }
}

function onCardClick(id, event) {
  // Only toggle on left mouse button
  if (event && typeof event.button !== 'undefined') {
    if (event.button !== 0) return;
  }
  toggleSelect(id);
}

function formatTime(sec) {
  if (!sec || isNaN(sec)) return '00:00';
  const m = Math.floor(sec / 60).toString().padStart(2, '0');
  const s = Math.floor(sec % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

function formatFileSize(bytes) {
  if (!bytes || bytes === 0 || isNaN(bytes)) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const sizeIndex = Math.min(i, sizes.length - 1); // 배열 범위 체크
  return Math.round((bytes / Math.pow(k, sizeIndex)) * 100) / 100 + ' ' + sizes[sizeIndex];
}

const router = useRouter();
const summaryVideoStore = useSummaryVideoStore();

const selectedVideos = computed(() => {
  return items.value.filter(v => selectedIds.value.includes(v.id));
});

const currentChatMessages = computed(() => {
  if (chatSessions.value.length === 0) return [];
  return chatSessions.value[currentChatIndex.value]?.messages || [];
});

onMounted(() => {
  loadVideosFromStorage();
  // Summarize.vue에서 동영상이 추가되었을 때 이벤트 리스너
  window.addEventListener('search-videos-updated', loadVideosFromStorage);
});

onActivated(() => {
  if (items.value.length === 0) {
    loadVideosFromStorage();
  }
});

onBeforeUnmount(() => {
  window.removeEventListener('search-videos-updated', loadVideosFromStorage);
});

async function loadVideosFromStorage() {
  // 사용자 ID 확인
  const userId = localStorage.getItem("vss_user_id");
  if (!userId) {
    // 로그인하지 않은 경우 localStorage에서 로드 (기존 방식)
    const stored = localStorage.getItem("videoItems");
    if (!stored) return;
    items.value = JSON.parse(stored).map(v => {
      const displayUrl = v.displayUrl || v.url || v.originUrl || '';
      return {
        ...v,
        originUrl: v.originUrl || v.url || displayUrl,
        displayUrl: displayUrl,
        objectUrl: displayUrl.startsWith('blob:') ? displayUrl : null,
        progress: 0,
        fileSize: v.fileSize || null,
        width: v.width || null,
        height: v.height || null
      };
    });
    return;
  }

  // DB에서 동영상 목록 가져오기
  try {
    const response = await fetch(`http://localhost:8001/videos?user_id=${userId}`);
    if (!response.ok) {
      throw new Error('동영상 목록 조회 실패');
    }
    const data = await response.json();
    
    if (data.success && data.videos) {
      items.value = data.videos.map(v => ({
        id: v.id,
        title: v.title,
        originUrl: v.file_url,
        displayUrl: v.file_url,
        objectUrl: null,
        progress: 0,
        fileSize: v.fileSize || null,
        width: v.width || null,
        height: v.height || null,
        date: v.date || new Date().toISOString().slice(0, 10),
        dbId: v.id, // DB ID 저장
        videoId: v.video_id || null // VIA 서버의 video_id 저장 (요약된 경우 미디어 삭제용)
      }));
    }
  } catch (error) {
    console.error('동영상 목록 로드 실패:', error);
    // 실패 시 localStorage에서 로드 (기존 방식)
    const stored = localStorage.getItem("videoItems");
    if (stored) {
      items.value = JSON.parse(stored).map(v => {
        const displayUrl = v.displayUrl || v.url || v.originUrl || '';
        return {
          ...v,
          originUrl: v.originUrl || v.url || displayUrl,
          displayUrl: displayUrl,
          objectUrl: displayUrl.startsWith('blob:') ? displayUrl : null,
          progress: 0,
          fileSize: v.fileSize || null,
          width: v.width || null,
          height: v.height || null
        };
      });
    }
  }
}

function persistToStorage() {
  localStorage.setItem("videoItems", JSON.stringify(items.value.map(({ id, title, originUrl, displayUrl, date, fileSize, width, height }) => ({ 
    id, 
    title, 
    url: originUrl || displayUrl || '', 
    originUrl: originUrl || displayUrl || '',
    displayUrl: displayUrl || originUrl || '',
    date,
    fileSize: fileSize || null,
    width: width || null,
    height: height || null
  }))));
}

// 드래그 & 드롭 업로드 핸들러
function onDragOverUpload(e) {
  e.preventDefault();
  isDragOverUpload.value = true;
}

function onDragLeaveUpload(e) {
  e.preventDefault();
  // 자식 요소로 이동할 때는 드래그 상태 유지
  if (!e.currentTarget.contains(e.relatedTarget)) {
    isDragOverUpload.value = false;
  }
}

async function onDropUpload(e) {
  e.preventDefault();
  isDragOverUpload.value = false;
  
  const files = Array.from(e.dataTransfer.files ?? []).filter((file) => {
    if (!file.type.startsWith('video/')) {
      alert('동영상 파일만 업로드할 수 있습니다.');
      return false;
    }
    return true;
  });

  if (files.length === 0) return;
  
  // handleUpload와 동일한 로직 사용
  await processUploadFiles(files);
}

async function handleUpload(e) {
  const files = Array.from(e.target.files ?? []).filter((file) => {
    if (!file.type.startsWith('video/')) {
      alert('동영상 파일만 업로드할 수 있습니다.');
      return false;
    }
    return true;
  });

  if (files.length === 0) return;
  
  await processUploadFiles(files);
  
  if (e.target) e.target.value = '';
}

// 공통 업로드 처리 함수
async function processUploadFiles(files) {

  // 사용자 ID 확인
  const userId = localStorage.getItem("vss_user_id");
  if (!userId) {
    alert('로그인이 필요합니다.');
    return;
  }

  // DB에서 중복 파일명 체크
  try {
    const response = await fetch(`http://localhost:8001/videos?user_id=${userId}`);
    if (response.ok) {
      const data = await response.json();
      if (data.success && data.videos) {
        const existingFileNames = new Set(data.videos.map(v => v.title));
        const duplicateFiles = files.filter(file => existingFileNames.has(file.name));
        
        if (duplicateFiles.length > 0) {
          const duplicateNames = duplicateFiles.map(f => f.name).join(', ');
          alert(`이미 업로드된 동영상입니다: ${duplicateNames}`);
          return;
        }
      }
    }
  } catch (error) {
    console.warn('중복 체크 실패, 업로드 계속 진행:', error);
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
      
      // 즉시 로컬 ObjectURL 생성하여 미리보기 가능하게 함
      const objUrl = URL.createObjectURL(file);
      
      const newVideo = {
        id: data.video_id,
        title: file.name,
        originUrl: data.file_url,
        displayUrl: objUrl, // 즉시 로컬 미리보기용 ObjectURL 사용
        objectUrl: objUrl,
        date: new Date().toISOString().slice(0, 10),
        file,
        url: data.file_url,
        fileSize: file.size,
        width: null,
        height: null,
        dbId: data.video_id
      };

      // 업로드 완료된 동영상을 즉시 목록에 추가
      items.value.unshift(newVideo);
      
      // 프로그레스 바를 100%로 업데이트 (리스트에 추가된 후)
      const uploadItem = uploadProgress.value.find(u => u.id === uploadId);
      if (uploadItem) {
        uploadItem.progress = 100;
        uploadItem.status = '완료';
      }
      
      // DB에 저장되므로 localStorage 저장 불필요
      // persistToStorage();
    } catch (error) {
      console.error('동영상 업로드 실패:', error);
      const uploadItem = uploadProgress.value.find(u => u.id === uploadId);
      if (uploadItem) {
        uploadItem.status = `실패: ${error.message}`;
      }
      alert(`동영상 업로드 실패: ${error.message}`);
    }
  });
}

function handleAddButtonClick() {
  // 파일 입력 요소 클릭 트리거
  const fileInput = document.querySelector('input[type="file"]');
  if (fileInput) {
    fileInput.click();
  }
}

function toggleSelect(id) {
  const idx = selectedIds.value.indexOf(id);
  idx === -1 ? selectedIds.value.push(id) : selectedIds.value.splice(idx, 1);
}

function zoomVideo(video) {
  // 그리드 비디오 상태 캡처 후 그리드 재생 중이면 일시정지
  const gridEl = videoRefs.value[video.id];
  let currentT = 0;
  const wasPlaying = playingVideoIds.value.includes(video.id) && gridEl;
  if (gridEl) {
    currentT = gridEl.currentTime;
    if (wasPlaying) {
      // 그리드 비디오 재생 중이었다면 일시정지 후 재생 목록에서 제거 (확대 모달은 독립 재생 상태 사용)
      gridEl.pause();
      const idx = playingVideoIds.value.indexOf(video.id);
      if (idx !== -1) playingVideoIds.value.splice(idx, 1);
    }
  }
  zoomedVideo.value = video;
  isZoomed.value = true;
  zoomPlaying.value = wasPlaying; // 확대 모달 재생 상태 독립 관리
  zoomProgress.value = video.progress || 0; // 기존 진행률 초기화
  nextTick(() => {
    if (zoomVideoRef.value) {
      try {
        if (currentT > 0) zoomVideoRef.value.currentTime = currentT;
        if (zoomPlaying.value) zoomVideoRef.value.play();
      } catch (e) {
        console.warn('Zoom video sync 실패:', e);
      }
    }
  });
}

function unzoomVideo() {
  // 확대 모달 상태 -> 그리드 동기화 (최종 시점 반영)
  const zVideo = zoomedVideo.value;
  const zoomEl = zoomVideoRef.value;
  const wasPlaying = zoomEl && !zoomEl.paused && zoomPlaying.value;
  let currentT = 0;
  if (zoomEl) currentT = zoomEl.currentTime;

  isZoomed.value = false;
  zoomedVideo.value = null;
  nextTick(() => {
    if (zVideo) {
      const gridEl = videoRefs.value[zVideo.id];
      const item = items.value.find(v => v.id === zVideo.id);
      if (gridEl) {
        try {
          if (currentT > 0) gridEl.currentTime = currentT;
          if (wasPlaying) {
            gridEl.play();
          }
        } catch (e) {
          console.warn('Unzoom sync 실패:', e);
        }
      }
      // 확대 모달에서 조작한 진행률을 그리드에 반영
      if (item) item.progress = zoomProgress.value;
      // 재생 상태 동기화: 확대 모달 최종 재생 상태에 따라 그리드 재생 ID 목록 갱신
      const listIdx = playingVideoIds.value.indexOf(zVideo.id);
      if (wasPlaying) {
        // 모달에서 재생 중이었으므로 그리드에서도 재생 상태로 표시
        if (listIdx === -1) playingVideoIds.value.push(zVideo.id);
      } else {
        // 모달에서 정지 상태였으므로 그리드에서도 제거 및 일시정지 보장
        if (listIdx !== -1) playingVideoIds.value.splice(listIdx, 1);
        if (gridEl) {
          try { gridEl.pause(); } catch (e) { /* ignore */ }
        }
      }
    }
    zoomPlaying.value = false;
  });
}

// 동영상 삭제 시 관련 클립 찾기 및 삭제
async function deleteClipsForVideos(videosToDelete) {
  const clipUrls = [];
  const videoTitles = new Set(videosToDelete.map(v => v.title));
  const videoIds = new Set(videosToDelete.map(v => v.id));
  
  // 모든 채팅방의 메시지에서 삭제될 동영상과 관련된 클립 찾기
  chatSessions.value.forEach(chat => {
    if (chat.messages) {
      chat.messages.forEach(message => {
        if (message.clips && Array.isArray(message.clips)) {
          message.clips.forEach(clip => {
            // sourceVideo나 title로 매칭
            const isRelated = 
              (clip.sourceVideo && videoTitles.has(clip.sourceVideo)) ||
              (clip.video && videoTitles.has(clip.video)) ||
              (message.selectedVideos && message.selectedVideos.some(v => videoIds.has(v.id)));
            
            if (isRelated && clip.url && !clip.via_response) {
              clipUrls.push(clip.url);
            }
          });
        }
      });
    }
  });
  
  // 클립이 있으면 삭제 요청
  if (clipUrls.length > 0) {
    try {
      const response = await fetch('http://localhost:8001/delete-clips', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          clip_urls: clipUrls
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log(`동영상 삭제: ${data.deleted_count}개의 관련 클립이 삭제되었습니다.`);
      } else {
        console.warn('클립 삭제 실패:', response.status);
      }
    } catch (error) {
      console.error('클립 삭제 중 오류:', error);
    }
  }
}

async function confirmDelete() {
  // 사용자 ID 확인
  const userId = localStorage.getItem("vss_user_id");
  
  // 선택된 동영상 삭제
  const videosToDelete = items.value.filter(video => selectedIds.value.includes(video.id));
  
  console.log('삭제할 동영상:', videosToDelete.map(v => ({ id: v.id, dbId: v.dbId, videoId: v.videoId, title: v.title })));
  
  // 동영상 삭제 전에 관련 클립 삭제
  await deleteClipsForVideos(videosToDelete);
  
  // VIA 서버에서 미디어 삭제 (video_id가 있는 경우)
  const mediaIdsToDelete = videosToDelete
    .map(v => v.videoId)
    .filter(id => id != null); // null이 아닌 것만 필터링
  
  if (mediaIdsToDelete.length > 0) {
    await removeMediaFromServer(mediaIdsToDelete);
  }
  
  // DB에서 삭제 (dbId가 있는 경우)
  if (userId) {
    const deletePromises = videosToDelete
      .filter(video => video.dbId) // dbId가 있는 동영상만
      .map(async (video) => {
        try {
          console.log(`DB 삭제 시도: video_id=${video.dbId}, user_id=${userId}`);
          const response = await fetch(`http://localhost:8001/videos/${video.dbId}?user_id=${userId}`, {
            method: 'DELETE'
          });
          
          if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: '응답 파싱 실패' }));
            console.error(`동영상 삭제 실패 (ID: ${video.dbId}):`, errorData);
            alert(`동영상 삭제 실패: ${errorData.detail || '알 수 없는 오류'}`);
          } else {
            const result = await response.json();
            console.log(`동영상 삭제 성공 (ID: ${video.dbId}):`, result);
          }
        } catch (error) {
          console.error(`동영상 삭제 중 오류 (ID: ${video.dbId}):`, error);
          alert(`동영상 삭제 중 오류가 발생했습니다: ${error.message}`);
        }
      });
    
    await Promise.all(deletePromises);
  } else {
    console.warn('사용자 ID가 없어 DB 삭제를 건너뜁니다.');
  }

  // 로컬에서 삭제
  items.value = items.value.filter(video => {
    if (selectedIds.value.includes(video.id)) {
      if (video.objectUrl) {
        try {
          URL.revokeObjectURL(video.objectUrl);
        } catch (error) {
          console.error("Failed to revoke object URL:", error);
        }
      }
      return false; // 삭제 대상
    }
    return true; // 유지 대상
  });

  // localStorage 업데이트
  persistToStorage();

  // 선택된 ID 초기화
  selectedIds.value = [];
  showDeletePopup.value = false;
}

function goToSummary() {
  const selectedVideos = items.value.filter(v => selectedIds.value.includes(v.id));
  summaryVideoStore.setVideos(selectedVideos); // Pinia 스토어에 선택된 동영상 저장
  router.push({ name: 'Summarize' }); // Summarize 페이지로 이동
}

function goToSearch() {
  if (selectedIds.value.length === 0) {
    return;
  }

  const selectionVideos = selectedVideos.value;
  const selectionSignature = getSelectionSignature(selectionVideos);

  showSearchSidebar.value = true;
  // 채팅 내역은 유지하고 입력창만 초기화
  searchInput.value = '';

  if (chatSessions.value.length === 0) {
    createNewChat(selectionVideos, selectionSignature);
    return;
  }

  const existingIndex = chatSessions.value.findIndex(
    chat => chat.selectionSignature === selectionSignature
  );

  if (existingIndex !== -1) {
    currentChatIndex.value = existingIndex;
    nextTick(() => {
      scrollToBottom();
    });
  } else {
    createNewChat(selectionVideos, selectionSignature);
  }
}

function closeSearchSidebar() {
  showSearchSidebar.value = false;
  // 채팅 내역은 유지하고 입력창만 초기화
  searchInput.value = '';
}

function getCurrentTime() {
  const now = new Date();
  const hours = now.getHours().toString().padStart(2, '0');
  const minutes = now.getMinutes().toString().padStart(2, '0');
  return `${hours}:${minutes}`;
}

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
    }
  });
}

function getSelectionSignature(videos) {
  if (!videos || videos.length === 0) return 'none';
  const ids = videos
    .map(video => video?.id)
    .filter(id => id !== undefined && id !== null)
    .map(id => id.toString())
    .sort();
  return ids.length > 0 ? ids.join('|') : 'none';
}

function snapshotVideosForChat(videos) {
  return (videos || []).map(video => ({
    id: video.id,
    title: video.title,
    displayUrl: video.displayUrl,
    date: video.date
  }));
}

function createNewChat(videos = selectedVideos.value, signature) {
  const effectiveVideos = videos || [];
  const selectionSnapshot = snapshotVideosForChat(effectiveVideos);
  const resolvedSignature = signature ?? getSelectionSignature(effectiveVideos);

  const newChat = {
    id: Date.now(),
    name: null, // 사용자가 수정할 수 있는 이름
    messages: [],
    selectionSignature: resolvedSignature
  };

  // 초기 시스템 메시지 추가
  newChat.messages.push({
    role: 'assistant',
    content: `안녕하세요! 선택하신 <strong>${selectionSnapshot.length}개의 동영상</strong>에서 검색을 도와드리겠습니다.`,
    isInitial: true,
    selectedVideos: selectionSnapshot,
    timestamp: getCurrentTime()
  });

  chatSessions.value.push(newChat);
  currentChatIndex.value = chatSessions.value.length - 1;

  nextTick(() => {
    scrollToBottom();
  });
}

function handleNewChatButtonClick() {
  // 사이드바가 닫혀있으면 먼저 열기
  if (!showSearchSidebar.value) {
    showSearchSidebar.value = true;
  }
  
  // 선택된 비디오가 있으면 그것으로, 없으면 빈 배열로 새 채팅방 생성
  const selectionVideos = selectedVideos.value;
  const selectionSignature = getSelectionSignature(selectionVideos);
  
  // 입력창 초기화
  searchInput.value = '';
  
  // 새 채팅방 생성
  createNewChat(selectionVideos, selectionSignature);

  nextTick(() => {
    scrollToBottom();
  });
}

function startEditChatName(index) {
  editingChatIndex.value = index;
  editingChatName.value = chatSessions.value[index].name || `채팅 ${index + 1}`;
  nextTick(() => {
    const input = Array.isArray(chatNameInput.value) ? chatNameInput.value[0] : chatNameInput.value;
    if (input) {
      input.focus();
      input.select();
    }
  });
}

function saveChatName(index) {
  if (editingChatIndex.value === index) {
    const trimmedName = editingChatName.value.trim();
    if (trimmedName) {
      chatSessions.value[index].name = trimmedName;
    } else {
      chatSessions.value[index].name = null;
    }
    editingChatIndex.value = null;
    editingChatName.value = '';
  }
}

function cancelEditChatName() {
  editingChatIndex.value = null;
  editingChatName.value = '';
}

function switchChat(index) {
  if (index >= 0 && index < chatSessions.value.length) {
    currentChatIndex.value = index;
    nextTick(() => {
      scrollToBottom();
    });
  }
}

async function deleteChat(index) {
  if (chatSessions.value.length <= 1) return; // 마지막 채팅창은 삭제 불가

  const chatToDelete = chatSessions.value[index];
  
  // 삭제할 채팅방의 모든 클립 URL 수집
  const clipUrls = [];
  if (chatToDelete.messages) {
    chatToDelete.messages.forEach(message => {
      if (message.clips && Array.isArray(message.clips)) {
        message.clips.forEach(clip => {
          if (clip.url && !clip.via_response) {
            clipUrls.push(clip.url);
          }
        });
      }
    });
  }
  
  // 클립이 있으면 삭제 요청
  if (clipUrls.length > 0) {
    try {
      const response = await fetch('http://localhost:8001/delete-clips', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          clip_urls: clipUrls
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log(`채팅방 삭제: ${data.deleted_count}개의 클립이 삭제되었습니다.`);
      } else {
        console.warn('클립 삭제 실패:', response.status);
      }
    } catch (error) {
      console.error('클립 삭제 중 오류:', error);
    }
  }

  chatSessions.value.splice(index, 1);

  // 삭제된 채팅창이 현재 채팅창이거나 그 이후인 경우 인덱스 조정
  if (currentChatIndex.value >= index) {
    currentChatIndex.value = Math.max(0, currentChatIndex.value - 1);
  }

  // 현재 채팅창이 범위를 벗어난 경우 마지막 채팅창으로 이동
  if (currentChatIndex.value >= chatSessions.value.length) {
    currentChatIndex.value = chatSessions.value.length - 1;
  }
}

async function ensureVideoFile(video) {
  if (video.file instanceof File) {
    return video.file;
  }

  if (!video.displayUrl) {
    return null;
  }

  try {
    const response = await fetch(video.displayUrl);
    if (!response.ok) {
      throw new Error(`Failed to fetch video blob (${response.status})`);
    }
    const blob = await response.blob();
    const filename = video.title || `video-${video.id}.mp4`;
    const file = new File([blob], filename, { type: blob.type || 'video/mp4' });
    video.file = file;
    return file;
  } catch (error) {
    console.error('Failed to reconstruct File from video URL:', error);
    return null;
  }
}

async function collectSelectedFiles() {
  const results = [];
  for (const video of selectedVideos.value) {
    const file = await ensureVideoFile(video);
    if (file) {
      results.push({ file, video });
    }
  }
  return results;
}

async function handleSearch() {
  const query = searchInput.value.trim();
  if (!query || isSearching.value) return;
  if (chatSessions.value.length === 0) return;

  const currentChat = chatSessions.value[currentChatIndex.value];

  currentChat.messages.push({
    content: query,
    role: "user",
    timestamp: getCurrentTime()
  });

  searchInput.value = '';
  scrollToBottom();

  isSearching.value = true;

  try {
    const fileEntries = await collectSelectedFiles();
    if (fileEntries.length === 0) {
      currentChat.messages.push({
        role: 'assistant',
        content: '선택된 동영상을 가져오지 못했습니다. 다시 시도해주세요.',
        timestamp: getCurrentTime()
      });
      return;
    }

    const userId = localStorage.getItem("vss_user_id");
    
    // 파일명과 video_id 매핑 생성
    const videoIdMap = {};
    fileEntries.forEach(({ file, video }) => {
      const dbId = video.dbId || video.id;
      if (dbId) {
        videoIdMap[file.name] = dbId;
      }
    });

    const formData = new FormData();
    fileEntries.forEach(({ file }) => {
      formData.append('files', file, file.name);
      formData.append('prompt', query);
    });
    
    // user_id와 video_ids 전달 (요약 결과 확인용)
    if (userId) {
      formData.append('user_id', userId);
    }
    if (Object.keys(videoIdMap).length > 0) {
      formData.append('video_ids', JSON.stringify(videoIdMap));
    }

    const response = await fetch(apiConfig.endpoints.generateClips, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}`);
    }

    const data = await response.json();
    const clips_extracted = data.clips_extracted || false; // 클립 추출 여부
    const groupedClipItems = (data.clips || []).map(group => ({
      video: group.video,
      clips: Array.isArray(group.clips) ? group.clips : []
    }));

    // 실제 URL이 있는 클립만 필터링 (via_response만 있는 것은 제외)
    // 타임스탬프 간격이 0초인 클립도 제외
    const validClips = groupedClipItems.flatMap(group =>
      group.clips
        .filter(clip => {
          // url이 있고 via_response가 없는 것만
          if (!clip.url || clip.via_response) return false;
          // 타임스탬프 간격이 0초 이하인 클립 제외
          if (clip.start_time !== undefined && clip.end_time !== undefined) {
            if (clip.end_time - clip.start_time <= 0) return false;
          }
          return true;
        })
        .map(clip => ({
          ...clip,
          sourceVideo: group.video
        }))
    );

    if (!clips_extracted || validClips.length === 0) {
      // 클립이 추출되지 않았을 경우
      currentChat.messages.push({
        role: 'assistant',
        content: '해당하는 장면이 없습니다.',
        timestamp: getCurrentTime()
      });
      return;
    }

    // 클립이 추출되었을 경우: 클립 동영상과 타임스탬프 표시
    currentChat.messages.push({
      role: 'assistant',
      content: `${groupedClipItems.length}개의 동영상에서 ${validClips.length}개의 장면을 찾았습니다.`,
      clips: validClips,
      groupedClips: groupedClipItems,
      timestamp: getCurrentTime()
    });
  } catch (error) {
    console.error('Search request failed:', error);
    currentChat.messages.push({
      role: 'assistant',
      content: `검색 중 오류가 발생했습니다. (${error.message})`,
      timestamp: getCurrentTime()
    });
  } finally {
    isSearching.value = false;
    scrollToBottom();
  }
}

// 채팅 클립 확대용(그리드 비디오와 구분되는 최소 필드 구성)
function zoomClip(clip) {
  // clip 객체를 확대 모달이 사용하는 형태로 매핑
  zoomedVideo.value = {
    id: `clip-${clip.id}`,
    title: clip.title || '클립',
    displayUrl: clip.url,
    progress: 0
  };
  isZoomed.value = true;
  zoomPlaying.value = false;
  zoomProgress.value = 0;
  nextTick(() => {
    const el = zoomVideoRef.value;
    if (!el) return;
    // 메타데이터가 준비될 때까지 기다린 뒤 재생
    if (!isFinite(el.duration)) {
      el.addEventListener('loadedmetadata', () => {
        try { el.currentTime = 0; el.play(); zoomPlaying.value = true; } catch (e) { console.warn('클립 모달 재생 실패:', e); }
      }, { once: true });
    } else {
      try { el.currentTime = 0; el.play(); zoomPlaying.value = true; } catch (e) { console.warn('클립 모달 재생 실패:', e); }
    }
  });
}

// 사이드바가 열릴 때 스크롤 초기화
watch(showSearchSidebar, (newVal) => {
  if (newVal) {
    nextTick(() => {
      scrollToBottom();
    });
  }
});

function togglePlay(videoId) {
  // 확대 모달 재생은 별도 상태 사용
  if (zoomedVideo.value && zoomedVideo.value.id === videoId && zoomVideoRef.value) {
    const el = zoomVideoRef.value;
    if (!el || !el.src) {
      console.warn('togglePlay: zoom video has no src');
      return;
    }
    if (!zoomPlaying.value) {
      // 안전하게 재생: 메타데이터가 로드될 때까지 대기
      if (!isFinite(el.duration)) {
        el.addEventListener('loadedmetadata', () => {
          el.play().then(() => { zoomPlaying.value = true; }).catch(e => {
            console.warn('zoom play failed:', e);
          });
        }, { once: true });
      } else {
        el.play().then(() => { zoomPlaying.value = true; }).catch(e => console.warn('zoom play failed:', e));
      }
    } else {
      try { el.pause(); } catch (e) { /* ignore */ }
      zoomPlaying.value = false;
    }
    return;
  }

  // 그리드 비디오 토글 (기존 로직)
  const videoElement = videoRefs.value[videoId];
  if (!videoElement) return;
  const index = playingVideoIds.value.indexOf(videoId);
  if (index === -1) {
    if (!videoElement.src) {
      console.warn('togglePlay: video element has no src');
      return;
    }
    playingVideoIds.value.push(videoId);
    if (!isFinite(videoElement.duration)) {
      videoElement.addEventListener('loadedmetadata', () => {
        videoElement.play().catch(e => console.warn('grid video play failed:', e));
      }, { once: true });
    } else {
      videoElement.play().catch(e => console.warn('grid video play failed:', e));
    }
  } else {
    playingVideoIds.value.splice(index, 1);
    videoElement.pause();
  }
}

function onVideoMetadataLoaded(videoId, event) {
  const video = items.value.find(v => v.id === videoId);
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

function updateProgress(videoId, event) {
  const video = items.value.find(v => v.id === videoId);
  if (video) {
    const { currentTime, duration } = event.target;
    video.progress = duration ? (currentTime / duration) * 100 : 0;
    currentTimeMap.value[videoId] = currentTime;
    if (duration && isFinite(duration)) {
      durationMap.value[videoId] = duration;
    }
  }
}

function onZoomTimeUpdate(event) {
  const { currentTime, duration } = event.target;
  zoomProgress.value = duration ? (currentTime / duration) * 100 : 0;
  zoomCurrentTime.value = currentTime || 0;
  zoomDuration.value = duration || 0;
}

function seekVideo(videoId, event) {
  if (zoomedVideo.value && zoomedVideo.value.id === videoId && zoomVideoRef.value) {
    const videoElement = zoomVideoRef.value;
    if (!videoElement || !videoElement.src) return;
    const { left, width } = event.currentTarget.getBoundingClientRect();
    const pct = Math.max(0, Math.min((event.clientX - left) / width, 1));
    const targetTime = pct * (isFinite(videoElement.duration) ? videoElement.duration : 0);
    if (!isFinite(targetTime)) return;
    try {
      videoElement.currentTime = targetTime;
    } catch (e) {
      console.warn('seekVideo(zoom) failed:', e);
    }
    zoomProgress.value = pct * 100;
    zoomCurrentTime.value = videoElement.currentTime;
    zoomDuration.value = videoElement.duration || 0;
    return;
  }
  const videoElement = videoRefs.value[videoId];
  if (!videoElement) return;
  if (!videoElement.src) return;
  const { left, width } = event.currentTarget.getBoundingClientRect();
  const pct = Math.max(0, Math.min((event.clientX - left) / width, 1));
  const targetTime = pct * (isFinite(videoElement.duration) ? videoElement.duration : 0);
  if (!isFinite(targetTime)) return;
  try {
    videoElement.currentTime = targetTime;
  } catch (e) {
    console.warn('seekVideo(grid) failed:', e);
  }
}

function startDragging(videoId, evt) {
  isDragging.value = true;
  draggedVideoId.value = videoId;
  // 확대 모달의 경우 zoomProgressBarRef 사용
  if (zoomedVideo.value && zoomedVideo.value.id === videoId) {
    draggingBarEl = zoomProgressBarRef.value;
  } else {
    // 진행바 엘리먼트 확보 (ref 사용, 없으면 이벤트 타겟에서 추론)
    draggingBarEl = progressBarRefs.value[videoId] || (evt && evt.target && evt.target.closest('.relative.cursor-pointer'));
  }
  document.addEventListener('mousemove', handleDragging);
  document.addEventListener('mouseup', stopDragging);
  if (evt) evt.preventDefault();
}

function handleDragging(event) {
  if (!isDragging.value || !draggedVideoId.value) return;

  // 확대 모달 드래그 처리 (독립 진행률)
  if (zoomedVideo.value && zoomedVideo.value.id === draggedVideoId.value && zoomVideoRef.value) {
    const videoElement = zoomVideoRef.value;
    if (!videoElement.duration) return;
    const progressBarEl = zoomProgressBarRef.value;
    if (!progressBarEl) return;
    const { left, width } = progressBarEl.getBoundingClientRect();
    const clickX = event.clientX - left;
    const percentage = Math.max(0, Math.min(clickX / width, 1));
    videoElement.currentTime = percentage * videoElement.duration;
    zoomProgress.value = percentage * 100;
    zoomCurrentTime.value = videoElement.currentTime;
    zoomDuration.value = videoElement.duration || 0;
    return;
  }

  // 그리드 드래그 처리
  const videoElement = videoRefs.value[draggedVideoId.value];
  if (!videoElement || !videoElement.duration) return;
  if (!draggingBarEl) return;
  const { left, width } = draggingBarEl.getBoundingClientRect();
  const clickX = event.clientX - left;
  const percentage = Math.max(0, Math.min(clickX / width, 1));
  videoElement.currentTime = percentage * videoElement.duration;
  const video = items.value.find(v => v.id === draggedVideoId.value);
  if (video) video.progress = percentage * 100;
}

function stopDragging() {
  isDragging.value = false;
  draggedVideoId.value = null;
  draggingBarEl = null;
  document.removeEventListener('mousemove', handleDragging);
  document.removeEventListener('mouseup', stopDragging);
}

// 업로드 모달 닫기
function closeUploadModal() {
  if (allUploadsComplete.value) {
    showUploadModal.value = false;
    uploadProgress.value = [];
  }
}

// 모든 업로드 완료 여부
const allUploadsComplete = computed(() => {
  return uploadProgress.value.length > 0 && 
         uploadProgress.value.every(u => u.progress === 100 || u.status === '완료' || u.status === '실패');
});

// 서버에서 미디어 삭제하는 함수
async function removeMediaFromServer(mediaIds) {
  if (!mediaIds || mediaIds.length === 0) return;

  const VSS_API_URL = 'http://localhost:8001/remove-media';

  try {
    const response = await fetch(VSS_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ media_ids: mediaIds })
    });

    if (!response.ok) {
      console.warn('서버 미디어 삭제 실패:', response.status);
      return false;
    }

    const data = await response.json();
    console.log('서버 미디어 삭제 성공:', data);
    return true;
  } catch (error) {
    console.warn('서버 미디어 삭제 중 오류:', error);
    return false;
  }
}

// XMLHttpRequest를 사용한 업로드 함수 (진행률 추적)
function uploadVideoWithProgress(file, userId, uploadId) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId);

    // 타임아웃 설정 (10분 = 600000ms, 큰 파일 업로드를 고려)
    xhr.timeout = 600000; // 10분

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
            uploadItem.status = '실패: 응답 파싱 오류';
            uploadItem.progress = 0;
          }
          reject(new Error('응답 파싱 실패'));
        }
      } else {
        const uploadItem = uploadProgress.value.find(u => u.id === uploadId);
        if (uploadItem) {
          uploadItem.status = `실패: HTTP ${xhr.status}`;
          uploadItem.progress = 0;
        }
        reject(new Error(`업로드 실패: ${xhr.status}`));
      }
    });

    // 타임아웃 처리
    xhr.addEventListener('timeout', () => {
      const uploadItem = uploadProgress.value.find(u => u.id === uploadId);
      if (uploadItem) {
        uploadItem.status = '실패: 타임아웃 (서버 응답 없음)';
        uploadItem.progress = 0;
      }
      reject(new Error('업로드 타임아웃: 서버 응답이 없습니다.'));
    });

    // 에러 처리
    xhr.addEventListener('error', () => {
      const uploadItem = uploadProgress.value.find(u => u.id === uploadId);
      if (uploadItem) {
        uploadItem.status = '실패: 네트워크 오류';
        uploadItem.progress = 0;
      }
      reject(new Error('네트워크 오류'));
    });

    // 중단(abort) 처리
    xhr.addEventListener('abort', () => {
      const uploadItem = uploadProgress.value.find(u => u.id === uploadId);
      if (uploadItem) {
        uploadItem.status = '취소됨';
        uploadItem.progress = 0;
      }
      reject(new Error('업로드가 취소되었습니다.'));
    });

    try {
      xhr.open('POST', 'http://localhost:8001/upload-video');
      xhr.send(formData);
    } catch (error) {
      const uploadItem = uploadProgress.value.find(u => u.id === uploadId);
      if (uploadItem) {
        uploadItem.status = `실패: ${error.message}`;
        uploadItem.progress = 0;
      }
      reject(error);
    }
  });
}

</script>

<style scoped>
/* 사이드바 애니메이션 */
.sidebar-enter-active,
.sidebar-leave-active {
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar-enter-from {
  transform: translateX(100%);
}

.sidebar-enter-to {
  transform: translateX(0);
}

.sidebar-leave-from {
  transform: translateX(0);
}

.sidebar-leave-to {
  transform: translateX(100%);
}
</style>
