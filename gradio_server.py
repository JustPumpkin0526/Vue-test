import gradio as gr

def summarize_video(video, prompt):
    # 여기에 비디오 요약 로직 구현
    return f"요약 결과: {prompt} (비디오 파일명: {video.name})"

iface = gr.Interface(
    fn=summarize_video,
    inputs=[gr.Video(label="Video"), gr.Textbox(label="Prompt")],
    outputs="text"
)

iface.launch(server_name="0.0.0.0", server_port=7100)