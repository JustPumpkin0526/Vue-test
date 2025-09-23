import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'

export function useVssUi() {
  /** -------------------------
   * Tabs
   * ------------------------- */
  const tabs = ['VIDEO FILE SUMMARIZATION & Q&A']
  const activeTab = ref(tabs[0])

  /** -------------------------
   * Dropdown (Chunk Size)
   * ------------------------- */
  const open = ref(false)
  const dropdownRef = ref(null)
  const options = [
    { value: 0, label: 'No Chunking' },
    { value: 5, label: '5 sec' },
    { value: 10, label: '10 sec' },
    { value: 20, label: '20 sec' },
    { value: 30, label: '30 sec' },
    { value: 60, label: '1 min' },
    { value: 120, label: '2 min' },
    { value: 300, label: '5 min' },
    { value: 600, label: '10 min' },
    { value: 1200, label: '20 min' },
    { value: 1800, label: '30 min' },
  ]
  const selected = ref(options[0].value)
  const selectedLabel = computed(
    () => options.find(o => o.value === selected.value)?.label ?? 'Select Chunk Size'
  )

  function toggleDropdown() {
    open.value = !open.value
  }
  function selectOption(option) {
    selected.value = option.value
    open.value = false
  }
  function onDocClick(e) {
    if (dropdownRef.value && !dropdownRef.value.contains(e.target)) {
      open.value = false
    }
  }

  /** -------------------------
   * File Upload / Video
   * ------------------------- */
  const fileInput = ref(null)
  const files = ref([])
  const videoUrl = ref(null)

  function triggerFileInput() {
    fileInput.value?.click()
  }

  function handleFile(file) {
    if (file && file.type.startsWith('video/')) {
      files.value.push(file)
      videoUrl.value = URL.createObjectURL(file)
    } else {
      alert('동영상 파일만 업로드할 수 있습니다.')
    }
  }

  function handleFileUpload(e) {
    handleFile((e.target.files || [])[0])
  }

  function handleDrop(e) {
    handleFile((e.dataTransfer?.files || [])[0])
  }

  function resetVideo() {
    if (!videoUrl.value) return
    videoUrl.value = null
    files.value = []
    if (fileInput.value) fileInput.value.value = null
  }

  /** -------------------------
   * Prompts & Accordion
   * ------------------------- */
  const prompts = reactive({
    general:
      'Write a concise and clear dense caption for the provided warehouse video, focusing on irregular or hazardous events such as boxes falling, workers not wearing PPE, workers falling, workers taking photographs, workers chitchatting, forklift stuck, etc. Start and end each sentence with a time stamp.',
    caption:
      "You should summarize the following events of a warehouse in the format start_time:end_time:caption. For start_time and end_time use . to seperate seconds, minutes, hours. If during a time segment only regular activities happen, then ignore them, else note any irregular activities in detail. The output should be bullet points in the format start_time:end_time: detailed_event_description. Don't return anything else except the bullet points.",
    aggregation:
      'You are a warehouse monitoring system. Given the caption in the form start_time:end_time: caption, Aggregate the following captions in the format start_time:end_time:event_description. If the event_description is the same as another event_description, aggregate the captions in the format start_time1:end_time1,...,start_timek:end_timek:event_description. If any two adjacent end_time1 and start_time2 is within a few tenths of a second, merge the captions in the format start_time1:end_time2. The output should only contain bullet points.  Cluster the output into Unsafe Behavior, Operational Inefficiencies, Potential Equipment Damage and Unauthorized Personnel',
  })

  const accordionItems = reactive([
    { label: 'Prompt', model: prompts.general, open: false },
    { label: 'Caption Summarization Prompt', model: prompts.caption, open: false },
    { label: 'Summary Aggregation Prompt', model: prompts.aggregation, open: false },
  ])

  function toggleAccordion(i) {
    accordionItems[i].open = !accordionItems[i].open
  }

  /** -------------------------
   * Summarization API
   * ------------------------- */
  const response = ref('')
  const VSS_API_URL = 'http://localhost:7100/vss-summarize'

  async function submitFiles() {
    if (!files.value.length) {
      return alert('Please upload a video file first.')
    }

    const formData = new FormData()
    formData.append('file', files.value[0])
    formData.append('prompt', accordionItems[0].model)
    formData.append('csprompt', accordionItems[1].model)
    formData.append('saprompt', accordionItems[2].model)
    formData.append('chunk_duration', selected.value)

    response.value = '⏳ Sending video + prompt to backend for summarization...'

    try {
      const res = await fetch(VSS_API_URL, { method: 'POST', body: formData })
      const data = await res.json()
      response.value = `✅ Summarization Completed!\n\n${data.summary || JSON.stringify(data, null, 2)}`
    } catch {
      response.value = '❌ Failed to send video. Please check server.'
    }
  }

  /** -------------------------
   * Chat
   * ------------------------- */
  const question = ref('')

  function askQuestion() {
    if (!question.value) return
    response.value += `\n\nQ: ${question.value}\nA: Placeholder answer from API.`
    question.value = ''
  }

  function resetChat() {
    response.value = ''
  }

  /** -------------------------
   * Parameters Popup
   * ------------------------- */
  const isParamOpen = ref(false)
  const vlm = reactive({ numFrames: 0, width: 0, height: 0 })
  const gen = reactive({ temperature: 0.4, topP: 1, topK: 100, maxTokens: 512, seed: 1 })
  const rag = reactive({
    type: 'graph-rag',
    batchSize: 1,
    topK: 5,
    summarize: { topP: 0.7, temperature: 0.2, maxTokens: 2048, batchSize: 6 },
    chat: { topP: 0.7, temperature: 0.2, maxTokens: 512 },
    notification: { topP: 0.7, temperature: 0.2, maxTokens: 2048 },
  })

  function openParams() {
    isParamOpen.value = true
    document.documentElement.style.overflow = 'hidden'
  }

  function closeParams() {
    isParamOpen.value = false
    document.documentElement.style.overflow = ''
  }

  function applyParams() {
    // TODO: 서버 반영
    closeParams()
  }

  function onKeydown(e) {
    if (e.key === 'Escape' && isParamOpen.value) closeParams()
  }

  /** -------------------------
   * Lifecycle
   * ------------------------- */
  onMounted(() => {
    document.title = 'Video Search and Summarization UI'
    document.addEventListener('click', onDocClick)
    document.addEventListener('keydown', onKeydown)
  })

  onBeforeUnmount(() => {
    document.removeEventListener('click', onDocClick)
    document.removeEventListener('keydown', onKeydown)
  })

  /** -------------------------
   * Return API
   * ------------------------- */
  return {
    // Tabs
    tabs, activeTab,

    // Dropdown
    open, dropdownRef, options, selected, selectedLabel,
    toggleDropdown, selectOption,

    // File Upload
    fileInput, files, videoUrl,
    triggerFileInput, handleFileUpload, handleDrop, resetVideo,

    // Prompts & Accordion
    prompts, accordionItems, toggleAccordion,

    // Summarization
    response, submitFiles,

    // Chat
    question, askQuestion, resetChat,

    // Parameters
    isParamOpen, vlm, gen, rag,
    openParams, closeParams, applyParams,
  }
}
