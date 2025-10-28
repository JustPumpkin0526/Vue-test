import os
import json
import requests
import gradio as gr

class VSS:
    """Wrapper to call VSS REST APIs"""

    def __init__(self, host):

        self.host = host

        self.summarize_endpoint = self.host + "/summarize"
        self.query_endpoint = self.host + "/chat/completions"
        self.files_endpoint = self.host + "/files"
        self.models_endpoint = self.host + "/models"

        self.model = self.get_model()

        self.f_count = 0

    def check_response(self, response, json_format=True):
        print(f"Response Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Request Status: SUCCESS")
            if json_format:
                return response.json()
            else:
                return response.text
        else:
            print("Request Status: ERROR")
            print(response.text)
            raise Exception(
                f"VSS Request Failed: {response}\n{response.status_code}\n{response.text}"
            )

    def get_model(self):
        response = requests.get(self.models_endpoint)
        json_data = self.check_response(response)
        return json_data["data"][0]["id"]  # get configured model name

    def upload_video(self, video_path):
        files = {"file": (f"file_{self.f_count}", open(video_path, "rb"))}
        data = {"purpose": "vision", "media_type": "video"}
        response = requests.post(self.files_endpoint, data=data, files=files)
        self.f_count += 1
        json_data = self.check_response(response)
        return json_data.get("id")  # return uploaded file id

    def summarize_video(self, file_id, prompt, cs_prompt, sa_prompt, chunk_duration):
        body = {
            "id": file_id,
            "prompt": prompt,
            "caption_summarization_prompt": cs_prompt,
            "summary_aggregation_prompt": sa_prompt,
            "model": self.model,
            "chunk_duration": chunk_duration,
            "enable_chat": True,
        }

        response = requests.post(self.summarize_endpoint, json=body)

        # check response
        json_data = self.check_response(response)
        message_content = json_data["choices"][0]["message"]["content"]
        return message_content

    def query_video(self, file_id, query):
        body = {
            "id": file_id,
            "messages": [{"content": query, "role": "user"}],
            "model": self.model,
        }
        response = requests.post(self.query_endpoint, json=body)
        json_data = self.check_response(response)
        message_content = json_data["choices"][0]["message"]["content"]
        return message_content

# -----------------------------
# Config
# -----------------------------
vss = VSS("http://172.16.7.64:8100")

CHUNK_SIZES = [
    ("No chunking", 0),
    ("5 sec", 5),
    ("10 sec", 10),
    ("20 sec", 20),
    ("30 sec", 30),
    ("1 min", 60),
    ("2 min", 120),
    ("5 min", 300),
    ("10 min", 600),
    ("20 min", 1200),
    ("30 min", 1800),
]

DEFAULT_PROMPT = (
    "Write a concise and clear dense caption for the provided warehouse video, "
    "focusing on irregular or hazardous events such as boxes falling, workers not wearing PPE, "
    "workers falling, workers taking photographs, workers chitchatting, forklift stuck, etc. "
    "Start and end each sentence with a time stamp."
)
DEFAULT_CAPTION_PROMPT = (
    "You should summarize the following events of a warehouse in the format start_time:end_time:caption. "
    "For start_time and end_time use . to seperate seconds, minutes, hours. If during a time segment only regular "
    "activities happen, then ignore them, else note any irregular activities in detail. "
    "The output should be bullet points in the format start_time:end_time: detailed_event_description. "
    "Don't return anything else except the bullet points."
)
DEFAULT_AGG_PROMPT = (
    "You are a warehouse monitoring system. Given the caption in the form start_time:end_time: caption, "
    "Aggregate the following captions in the format start_time:end_time:event_description. "
    "If the event_description is the same as another event_description, aggregate the captions in the format "
    "start_time1:end_time1,...,start_timek:end_timek:event_description. "
    "If any two adjacent end_time1 and start_time2 is within a few tenths of a second, merge the captions "
    "in the format start_time1:end_time2. The output should only contain bullet points. "
    "Cluster the output into Unsafe Behavior, Operational Inefficiencies, Potential Equipment Damage and Unauthorized Personnel"
)

# -----------------------------
# Helpers
# -----------------------------
def _get_model_id():
    r = requests.get(vss.models_endpoint, timeout=30)
    r.raise_for_status()
    data = r.json()
    # 보통 첫 번째가 현재 서빙 모델
    return data["data"][0]["id"]

def _upload_video(path):
    with open(path, "rb") as f:
        files = {"file": (os.path.basename(path), f, "video/*")}
        data = {"purpose": "vision", "media_type": "video"}
        r = requests.post(vss.files_endpoint, data=data, files=files, timeout=300)
    r.raise_for_status()
    return r.json()["id"]

def _parse_sse_text(text):
    """
    NVIDIA NIM/VIA가 반환하는 스트리밍 SSE 텍스트를 파싱.
    각 줄이 'data: {...}' 형태. 마지막은 'data: [DONE]'.
    """
    outputs = []
    usage = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("data: "):
            continue
        payload = line[6:]
        if payload == "[DONE]":
            break
        try:
            obj = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if obj.get("choices"):
            outputs.append(obj)
        if obj.get("usage"):
            usage = obj["usage"]
    return outputs, usage

def _accumulate_content(items):
    """choices 배열을 합쳐서 보기 좋은 문자열로."""
    if not items:
        return ""
    # 단일 응답이면 content 바로 꺼냄
    if len(items) == 1:
        return items[0]["choices"][0]["message"]["content"]
    # 여러 청크면 구간 테이블 느낌으로 합치기
    rows = []
    for it in items:
        ch = it["choices"][0]["message"]["content"]
        if "media_info" in it:
            mi = it["media_info"]
            s = mi.get("start_offset")
            e = mi.get("end_offset")
            rows.append(f"[{s:.2f} → {e:.2f}] {ch}")
        else:
            rows.append(ch)
    return "\n".join(rows)

# -----------------------------
# Gradio Callbacks
# -----------------------------
def on_video_change(video_path):
    """비디오 업로드시 Summarize 버튼 활성화"""
    return gr.update(interactive=bool(video_path), value="Summarize")

def do_summarize(
    video_path,
    chunk_choice,  # tuple(label, value) 중 value만 넘김
    prompt,
    cs_prompt,
    agg_prompt,
    chat_history
):
    if not video_path:
        return chat_history, gr.update(value="Please upload a video first."), None

    try:
        model_id = _get_model_id()
    except Exception as e:
        return (
            chat_history + [{"role":"assistant","content":f"❌ /models error: {e}"}],
            gr.update(value="Models endpoint error. Check VSS."),
            None
        )

    try:
        file_id = _upload_video(video_path)
    except Exception as e:
        return (
            chat_history + [{"role":"assistant","content":f"❌ /files upload error: {e}"}],
            gr.update(value="Upload failed."),
            None
        )

    # chunk_duration (정수). “No chunking”도 백엔드가 허용. 기본 20s 권장 시 20으로 바꿔도 됨.
    chunk_duration = int(chunk_choice)

    payload = {
        "id": file_id,
        "model": model_id,
        "chunk_duration": chunk_duration,
        "temperature": 0.2,
        "top_p": 0.7,
        "max_tokens": 2048,
        "stream": True,
        "stream_options": {"include_usage": True},
        # 중요: 캡션→어그리게이션 프롬프트 항상 전달(“캡션이 없다” 방지)
        "prompt": prompt or DEFAULT_PROMPT,
        "caption_summarization_prompt": cs_prompt or DEFAULT_CAPTION_PROMPT,
        "summary_aggregation_prompt": agg_prompt or DEFAULT_AGG_PROMPT,
        "enable_chat": True,
        "enable_chat_history": True,
    }

    try:
        r = requests.post(vss.summarize_endpoint, json=payload, timeout=600)
        r.raise_for_status()
        items, usage = _parse_sse_text(r.text)
        content = _accumulate_content(items) or "(No summary generated.)"
        # 응답에 자주 보이는 “captions not provided” 방지: 위에서 프롬프트 강제 세팅함.
        chat_history = chat_history + [
            {"role":"assistant","content": f"**Summary**\n\n{content}"}
        ]
        return chat_history, gr.update(value="Summarization done."), file_id
    except Exception as e:
        return (
            chat_history + [{"role":"assistant","content":f"❌ /summarize error: {e}"}],
            gr.update(value="Summarization failed."),
            None
        )

def do_ask(question, file_id, chat_history):
    if not question:
        return chat_history
    chat_history = chat_history + [{"role":"user","content":question}]
    if not file_id:
        return chat_history + [{"role":"assistant","content":"Please summarize a video first."}]

    try:
        model_id = _get_model_id()
    except Exception as e:
        return chat_history + [{"role":"assistant","content":f"❌ /models error: {e}"}]

    payload = {
        "id": file_id,
        "model": model_id,
        "messages": [{"role":"user","content":question}],
        "temperature": 0.2,
        "top_p": 0.7,
        "max_tokens": 512,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    try:
        r = requests.post(vss.query_endpoint, json=payload, timeout=300)
        r.raise_for_status()
        items, _ = _parse_sse_text(r.text)
        content = _accumulate_content(items) or "(No answer.)"
        return chat_history + [{"role":"assistant","content":content}]
    except Exception as e:
        return chat_history + [{"role":"assistant","content":f"❌ /chat/completions error: {e}"}]

def do_reset():
    return []

# -----------------------------
# UI
# -----------------------------
with gr.Blocks(title="Video Search and Summarization (Gradio)") as demo:
    gr.Markdown("## VIDEO SEARCH AND SUMMARIZATION")

    with gr.Row():
        # Left
        with gr.Column(scale=1):
            video = gr.Video(label="Upload Video", sources=["upload"], show_download_button=False)
            chunk = gr.Dropdown(choices=CHUNK_SIZES, value=CHUNK_SIZES[0][1], label="CHUNK SIZE")
            prompt = gr.TextArea(label="Prompt", value=DEFAULT_PROMPT, lines=4)
            cs_prompt = gr.TextArea(label="Caption Summarization Prompt", value=DEFAULT_CAPTION_PROMPT, lines=5)
            agg_prompt = gr.TextArea(label="Summary Aggregation Prompt", value=DEFAULT_AGG_PROMPT, lines=6)

            summarize_btn = gr.Button("Select/Upload video to summarize", variant="primary", interactive=False)
            status = gr.Textbox(label="Status", value="Waiting for a video...", interactive=False)

        # Right
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(label="Response", height=450, type="messages")
            with gr.Row():
                question = gr.Textbox(label="Ask a question", scale=4)
                ask_btn = gr.Button("Ask", scale=1)
                reset_btn = gr.Button("Reset Chat", scale=1)

    # States
    file_id_state = gr.State(None)
    chat_state = gr.State([])  # messages 포맷

    # Events
    video.change(on_video_change, inputs=video, outputs=summarize_btn)

    summarize_btn.click(
        do_summarize,
        inputs=[video, chunk, prompt, cs_prompt, agg_prompt, chat_state],
        outputs=[chat_state, status, file_id_state]
    ).then(lambda h: gr.update(value=h), inputs=chat_state, outputs=chatbot)

    ask_btn.click(
        do_ask,
        inputs=[question, file_id_state, chat_state],
        outputs=[chat_state]
    ).then(lambda h: "", outputs=question).then(lambda h: gr.update(value=h), inputs=chat_state, outputs=chatbot)

    reset_btn.click(do_reset, inputs=None, outputs=[chat_state]).then(
        lambda h: gr.update(value=h), inputs=chat_state, outputs=chatbot
    )

if __name__ == "__main__":
    # 서버 바인딩은 0.0.0.0 가능하지만, 접속은 브라우저에서 http://localhost:7860 로!
    demo.launch(server_name="0.0.0.0", server_port=7860)