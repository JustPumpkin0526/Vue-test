<template>
  <!-- 메뉴 틀 -->
  <div id="video_list" class="w-[100%] h-[90vh]">

    <!-- 헤더 -->
    <header id="header" class="flex items-center justify-between">

      <button
        class="mt-4 mr-4 ml-auto bg-slate-600 hover:bg-slate-700 text-white px-5 py-2.5 rounded-xl shadow-sm cursor-pointer flex items-center gap-2 transform transition-all duration-300 hover:scale-105 active:scale-95 disabled:bg-gray-300 disabled:text-gray-100 disabled:shadow-none disabled:transform-none disabled:cursor-default"
        :disabled="items.length === 0" @click="allselect()">
        Select All
      </button>

      <!-- 업로드 버튼 -->
      <div class="flex items-center h-12 mr-12 mt-auto ">
        <label
          class="bg-slate-600 hover:bg-slate-700 text-white px-5 py-2.5 rounded-xl shadow-sm cursor-pointer flex items-center gap-2 transform transition-all duration-300 hover:scale-105 active:scale-95">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
          </svg>
          <span class="font-medium">Upload Video</span>
          <input type="file" accept="video/*" multiple class="hidden" @change="handleUpload" />
        </label>
      </div>

    </header>

    <!-- 비디오 리스트 -->
    <div id="list"
      class="relative w-full h-[90%] border border-gray-200 bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl p-6 mt-6 shadow-inner">

      <!-- 동영상 출력 영역 -->
      <div class="w-full h-[90%] border border-gray-200 bg-white rounded-2xl overflow-y-auto shadow-sm">
        <div v-if="items.length === 0" class="flex items-center justify-center h-full">
          <div
            class="w-[30%] h-[9%] bg-gradient-to-br from-gray-50 to-gray-100 text-gray-500 text-center text-[24px] pt-[22px] border border-gray-200 rounded-2xl shadow-sm backdrop-blur-sm">
            <p class="font-light">Please upload a video</p>
          </div>
        </div>

        <!-- 동영상 출력 그리드(행열 구조) -->
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6 p-6 overflow-y-auto">
          <div v-for="video in items" :key="video.id"
            class="flex flex-col items-center justify-center rounded-2xl shadow-md hover:shadow-xl cursor-pointer p-3 border border-gray-200 relative transform transition-all duration-300 hover:scale-105 hover:-translate-y-1 group"
            :class="{ 'ring-2 ring-blue-400 bg-blue-100': selectedIds.includes(video.id) }"
            @click="onCardClick(video.id, $event)" @contextmenu.prevent.stop="onVideoContextMenu(video, $event)">
            <div
              class="w-[100%] h-[100%] flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 rounded-xl mb-2 overflow-hidden relative group-hover:from-gray-200 group-hover:to-gray-300 transition-all duration-300"
              @mouseenter="hoveredVideoId = video.id" @mouseleave="hoveredVideoId = null">
              <video :ref="el => (videoRefs[video.id] = el)" v-if="video.displayUrl" :src="video.displayUrl"
                class="object-cover rounded-xl transition-transform duration-300 group-hover:scale-105"
                preload="metadata" @timeupdate="updateProgress(video.id, $event)"></video>
              <span v-else class="text-gray-400 text-sm">No Thumbnail</span>
              <!-- 그리드: 재생 중이 아닐 때 어두워지는 오버레이 -->
              <div v-if="video.displayUrl" class="absolute inset-0 pointer-events-none transition-colors duration-300"
                :class="playingVideoIds.includes(video.id) ? 'bg-transparent' : 'bg-black/20'"></div>
              <!-- 재생 버튼 -->
              <button @click.stop="togglePlay(video.id)" :class="{
                'opacity-100 scale-100': hoveredVideoId === video.id || !playingVideoIds.includes(video.id),
                'opacity-0 scale-90': hoveredVideoId !== video.id && playingVideoIds.includes(video.id),
              }"
                class="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-black/60 to-black/40 backdrop-blur-sm text-white rounded-full w-14 h-14 m-auto transition-all duration-300 hover:scale-110 active:scale-95">
                <svg v-if="!playingVideoIds.includes(video.id)" xmlns="http://www.w3.org/2000/svg" fill="currentColor"
                  viewBox="0.4 -0.7 16 16" class="w-8 h-8">
                  <path
                    d="M6.271 4.055a.5.5 0 0 1 .759-.429l4.592 3.11a.5.5 0 0 1 0 .828l-4.592 3.11a.5.5 0 0 1-.759-.429V4.055z" />
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0.4 -0.1 16 16"
                  class="w-8 h-8">
                  <path
                    d="M5.5 3.5A.5.5 0 0 1 6 3h1a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5H6a.5.5 0 0 1-.5-.5v-9zM9.5 3.5A.5.5 0 0 1 10 3h1a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-9z" />
                </svg>
              </button>
              <div
                class="absolute bottom-0 left-0 w-full px-2 pb-2 flex flex-col transition-all duration-300 ease-in-out"
                :class="{
                  'opacity-100 scale-100': hoveredVideoId === video.id || !playingVideoIds.includes(video.id),
                  'opacity-0 scale-90': hoveredVideoId !== video.id && playingVideoIds.includes(video.id),
                }">
                <div
                  class="relative w-full h-2 bg-gray-200/90 rounded-full cursor-pointer group/progress overflow-visible backdrop-blur-[2px] pointer-events-auto"
                  :class="{ 'dragging': isDragging && draggedVideoId === video.id }"
                  @click.stop="seekVideo(video.id, $event)">
                  <div class="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full shadow-sm overflow-hidden progress-bar-fill"
                    :class="{ 'transition-all duration-300': !(isDragging && draggedVideoId === video.id) }"
                    :style="{ width: `${video.progress || 0}%` }"></div>
                  <div
                    class="absolute top-1 h-4 w-4 bg-white rounded-full shadow-lg transform -translate-x-1/2 -translate-y-1/2 transition-all duration-200 border-2 border-slate-500 z-[100] progress-bar-handle"
                    :class="{ 'transition-none': isDragging && draggedVideoId === video.id }"
                    :style="{ left: `${video.progress || 0}%` }" @mousedown="startDragging(video.id, $event)"></div>
                </div>
                <div
                  class="flex justify-between mt-1 text-[10px] font-medium text-white drop-shadow pointer-events-none">
                  <span>{{ formatTime(currentTimeMap[video.id] || 0) }}</span>
                  <span>{{ formatTime(durationMap[video.id] || 0) }}</span>
                </div>
              </div>
            </div>
            <div v-if="video.title" class="ml-4 w-full text-sm font-medium text-gray-800 truncate text-left">
              {{ video.title }}
            </div>
          </div>
        </div>
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
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
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
                      class="absolute top-1/2 h-5 w-5 bg-white rounded-full shadow-lg transform -translate-x-1/2 -translate-y-1/2 transition-all duration-200 border-2 border-blue-500 z-[20]"
                      :class="{ 'transition-none': isDragging && draggedVideoId === zoomedVideo.id }"
                      :style="{ left: `${zoomProgress}%` }" @mousedown="startDragging(zoomedVideo.id)"></div>
                  </div>
                  <div class="flex items-center justify-between text-xs font-medium text-gray-600">
                    <div class="flex items-center gap-2">
                      <span v-if="zoomedVideo.title" class="text-sm font-semibold text-gray-800 truncate max-w-[50vw]">{{ zoomedVideo.title }}</span>
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
      <!-- 우클릭 컨텍스트 메뉴 (고정 위치) -->
      <div v-if="contextMenu.visible" class="fixed z-[200]"
        :style="{ left: `${contextMenu.x}px`, top: `${contextMenu.y}px` }" @click.stop>
        <div class="bg-white rounded-lg shadow-xl border border-gray-100 overflow-hidden w-[200px]">
          <button v-if="selectedIds.length < 2" class="w-full text-left px-4 py-3 hover:bg-gray-50" @click.stop="contextZoom">확대</button>
          <button class="w-full text-left px-4 py-3 hover:bg-gray-50" @click.stop="contextOpenSettings">설정</button>
          <button class="w-full text-left px-4 py-3 hover:bg-gray-50" @click.stop="contextSummary">Summary</button>
          <div class="h-px bg-gray-100"></div>
          <button class="w-full text-left px-4 py-3 text-red-600 hover:bg-gray-50" @click.stop="contextDelete">{{ selectedIds.length > 1 ? `선택된 항목 삭제 (${selectedIds.length})` : '삭제' }}</button>
        </div>
      </div>
      <!-- 좌측 하단 Summary, Search 버튼 -->
      <div class="absolute left-[2%] bottom-[4%] w-[21%] z-50 flex gap-4">
        <button
          class="w-[100%] text-[25px] px-5 py-3 rounded-xl bg-slate-600 hover:bg-slate-700 text-white shadow-sm disabled:bg-gray-300 disabled:text-gray-100 disabled:shadow-none disabled:transform-none disabled:cursor-default transition-all duration-300 transform hover:scale-105 active:scale-95 font-semibold"
          :disabled="selectedIds.length === 0" @click="goToSearch">Search</button>
        <button
          class="w-[100%] text-[25px] px-5 py-3 rounded-xl bg-slate-600 hover:bg-slate-700 text-white shadow-sm disabled:bg-gray-300 disabled:text-gray-100 disabled:shadow-none disabled:transform-none disabled:cursor-default transition-all duration-300 transform hover:scale-105 active:scale-95 font-semibold"
          :disabled="selectedIds.length === 0" @click="goToSummary">Summary</button>
      </div>

      <!-- 중앙 팝업창 -->
      <Transition name="modal">
        <div v-if="showDeletePopup"
          class="fixed inset-0 flex items-center justify-center z-[100] bg-black/50 backdrop-blur-sm">
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

      <!-- Search 사이드바 메뉴 -->
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
                <button @click="createNewChat"
                  class="relative p-2 hover:bg-gray-100 rounded-full transition-colors group" title="신규 채팅창 추가">
                  <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                  </svg>
                  <!-- 툴팁 -->
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
                      class="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
                      <video :src="video.displayUrl" class="w-12 h-8 object-cover rounded"></video>
                      <div class="flex-1 min-w-0">
                        <p class="text-xs font-medium text-gray-800 truncate">{{ video.title }}</p>
                        <p class="text-xs text-gray-500">{{ video.date }}</p>
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
                      :class="message.role === 'assistant' ? 'flex items-center gap-2 p-2 bg-gray-50 rounded-xl transition-all duration-200 hover:bg-gray-100' : 'flex items-center gap-2 p-2 bg-green-600/80 rounded-xl transition-all duration-200 hover:bg-green-600'">
                      <video :src="clip.url" class="w-12 h-8 object-cover rounded cursor-pointer" preload="metadata"
                        @click.stop="zoomClip(clip)" @error="(e) => console.warn('clip thumbnail error', e, clip.url)"
                        crossorigin="anonymous"></video>
                      <div class="flex-1 min-w-0">
                        <p
                          :class="message.role === 'assistant' ? 'text-xs font-medium text-gray-800 truncate' : 'text-xs font-medium text-white truncate'">
                          {{ clip.title }}</p>
                        <p :class="message.role === 'assistant' ? 'text-xs text-gray-500' : 'text-xs text-green-100'">{{
                          clip.sourceVideo || clip.date }}</p>
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
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
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

      <!-- Search Menu -->
      <div v-if="showSearchMenu" class="absolute top-4 right-4 z-50 bg-white p-4 rounded-lg shadow-lg">
        <h3 class="text-lg font-semibold mb-2">Search Scenes</h3>
        <input v-model="searchQuery" type="text" placeholder="Enter keyword..."
          class="border border-gray-300 rounded-lg px-4 py-2 w-full mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500" />
        <button @click="searchScenes"
          class="bg-blue-500 text-white px-4 py-2 rounded-lg shadow hover:bg-blue-600 transition w-full mb-2">
          Search
        </button>
        <button @click="closeSearchMenu"
          class="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg shadow hover:bg-gray-400 transition w-full">
          Close
        </button>

        <!-- Search Results -->
        <div v-if="searchResults.length > 0" class="mt-4">
          <h4 class="text-md font-medium mb-2">Results:</h4>
          <ul class="list-disc pl-5">
            <li v-for="scene in searchResults" :key="scene.id" class="mb-1">
              <button @click="goToScene(scene)" class="text-blue-500 hover:underline">
                {{ scene.description }} ({{ formatTime(scene.timestamp) }})
              </button>
            </li>
          </ul>
        </div>
        <div v-else-if="searchPerformed" class="mt-4 text-gray-500">
          No results found.
        </div>
      </div>
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
const expandedVideoId = ref(null);
const showDeletePopup = ref(false);
const items = ref([]);
const selectedIds = ref([]);
const videoRefs = ref({});
const isDragging = ref(false);
const draggedVideoId = ref(null);
const chatSessions = ref([]);
const currentChatIndex = ref(0);
const searchInput = ref('');
const isSearching = ref(false);
const chatContainer = ref(null);
const editingChatIndex = ref(null);
const editingChatName = ref('');
const chatNameInput = ref(null);
const showSearchMenu = ref(false);
const searchQuery = ref('');
const searchResults = ref([]);
const searchPerformed = ref(false);

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
  contextMenu.value = { visible: true, x: e.clientX, y: e.clientY, video };
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

function contextOpenSettings() {
  if (!contextMenu.value.video) return;
  openSettings(contextMenu.value.video.id);
  closeContextMenu();
}

function contextSummary() {
  goToSummary();
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

const router = useRouter();
const summaryVideoStore = useSummaryVideoStore();

const selectedVideos = computed(() => {
  return items.value.filter(v => selectedIds.value.includes(v.id));
});

const currentChatMessages = computed(() => {
  if (chatSessions.value.length === 0) return [];
  return chatSessions.value[currentChatIndex.value]?.messages || [];
});

onMounted(loadVideosFromStorage);
onActivated(() => {
  if (items.value.length === 0) {
    loadVideosFromStorage();
  }
});

function loadVideosFromStorage() {
  const stored = localStorage.getItem("videoItems");
  if (!stored) return;
  items.value = JSON.parse(stored).map(v => ({
    ...v,
    originUrl: v.url || v.originUrl || '',
    displayUrl: v.url || v.displayUrl || v.originUrl || '',
    objectUrl: null,
    progress: 0
  }));
}

function persistToStorage() {
  localStorage.setItem("videoItems", JSON.stringify(items.value.map(({ id, title, originUrl, date }) => ({ id, title, url: originUrl, date }))));
}

function handleUpload(e) {
  const files = Array.from(e.target.files ?? []).filter((file) => {
    if (!file.type.startsWith('video/')) {
      alert('동영상 파일만 업로드할 수 있습니다.');
      return false;
    }
    return true;
  });

  const newVideos = files.map((file) => {
    const objUrl = URL.createObjectURL(file);
    return {
      id: Date.now() + Math.random(),
      title: file.name,
      originUrl: objUrl,
      displayUrl: objUrl,
      objectUrl: objUrl,
      date: new Date().toISOString().slice(0, 10),
      file,
      url: objUrl
    };
  });

  items.value.unshift(...newVideos);
  persistToStorage();
  if (e.target) e.target.value = '';
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

function confirmDelete() {

  // 선택된 동영상 삭제
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
  router.push({ name: 'Summary' }); // Summary 페이지로 이동
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

function deleteChat(index) {
  if (chatSessions.value.length <= 1) return; // 마지막 채팅창은 삭제 불가

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

    const formData = new FormData();
    fileEntries.forEach(({ file }) => {
      formData.append('files', file, file.name);
    });

    const response = await fetch('http://localhost:8001/api/generate-clips', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}`);
    }

    const data = await response.json();
    const groupedClipItems = (data.clips || []).map(group => ({
      video: group.video,
      clips: Array.isArray(group.clips) ? group.clips : []
    }));

    const flattenedClips = groupedClipItems.flatMap(group =>
      group.clips.map(clip => ({
        ...clip,
        sourceVideo: group.video
      }))
    );

    if (flattenedClips.length === 0) {
      currentChat.messages.push({
        role: 'assistant',
        content: '클립이 추출되지 않았습니다.',
        timestamp: getCurrentTime()
      });
      return;
    }

    currentChat.messages.push({
      role: 'assistant',
      content: `${groupedClipItems.length}개의 동영상에서 ${flattenedClips.length}개의 클립을 추출했습니다.`,
      clips: flattenedClips,
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

function openSettings(videoId) {
  expandedVideoId.value = expandedVideoId.value === videoId ? null : videoId;
}

function updateProgress(videoId, event) {
  const video = items.value.find(v => v.id === videoId);
  if (video) {
    const { currentTime, duration } = event.target;
    video.progress = duration ? (currentTime / duration) * 100 : 0;
    currentTimeMap.value[videoId] = currentTime;
    durationMap.value[videoId] = duration;
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

function startDragging(videoId) {
  isDragging.value = true;
  draggedVideoId.value = videoId;

  document.addEventListener('mousemove', handleDragging);
  document.addEventListener('mouseup', stopDragging);
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

  // 그리드 드래그 처리 (기존 로직)
  const videoElement = videoRefs.value[draggedVideoId.value];
  if (!videoElement || !videoElement.duration) return;
  const videoContainer = videoElement.closest('.group');
  if (!videoContainer) return;
  const progressBar = videoContainer.querySelector('.group\\/progress');
  if (!progressBar) return;
  const { left, width } = progressBar.getBoundingClientRect();
  const clickX = event.clientX - left;
  const percentage = Math.max(0, Math.min(clickX / width, 1));
  videoElement.currentTime = percentage * videoElement.duration;
  const video = items.value.find(v => v.id === draggedVideoId.value);
  if (video) video.progress = percentage * 100;
}

function stopDragging() {
  isDragging.value = false;
  draggedVideoId.value = null;

  document.removeEventListener('mousemove', handleDragging);
  document.removeEventListener('mouseup', stopDragging);
}

// Mock data for scenes (replace with actual data or API call)
const scenes = ref([
  { id: 1, videoId: 101, description: 'Scene 1', timestamp: 30 },
  { id: 2, videoId: 101, description: 'Scene 2', timestamp: 120 },
  { id: 3, videoId: 102, description: 'Scene 3', timestamp: 45 },
]);

const searchScenes = () => {
  searchPerformed.value = true;
  if (!searchQuery.value) {
    searchResults.value = [];
    return;
  }

  // Filter scenes based on selected video IDs and search query
  searchResults.value = scenes.value.filter(
    scene => selectedIds.value.includes(scene.videoId) &&
      scene.description.toLowerCase().includes(searchQuery.value.toLowerCase())
  );
};

const closeSearchMenu = () => {
  showSearchMenu.value = false;
  searchQuery.value = '';
  searchResults.value = [];
  searchPerformed.value = false;
};
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
