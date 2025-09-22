import gradio as gr

def my_function(input1, input2):
    return f"{input1}" + f"{input2}"

demo = gr.Interface(
    fn=my_function,
    inputs=["text", "text", "text"],
    outputs="text"
)

demo.launch()