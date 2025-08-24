import gradio as gr
from openai import OpenAI
import re
# Connect to local vLLM server
client = OpenAI(base_url="http://localhost:8000/v1", api_key="any_key")

# Custom CSS for better LaTeX rendering
latex_css = """
<style>
.katex {
    font-size: 1.1em !important;
}
.katex-display {
    margin: 1em 0 !important;
}

/* Improve LaTeX rendering in dark/light themes */
.katex .base {
    color: inherit !important;
}
</style>
"""

def enhance_latex_rendering(text):
    """
    Enhance LaTeX rendering by ensuring proper formatting and escaping
    """
    # Fix common LaTeX formatting issues
    text = re.sub(r'\\\\(?!\\)', r'\\\\\\\\', text)  # Ensure proper line breaks
    
    # Ensure proper spacing around delimiters
    text = re.sub(r'\$([^$]+?)\$', r'$ \1 $', text)
    text = re.sub(r'\$ +([^$]+?) +\$', r'$\1$', text)  # Remove extra spaces
    
    return text

def chat_stream(message, history):
    # Convert Gradio history format to OpenAI format
    messages = []
    
    # Add conversation history
    for m in history:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": message})

    stream = client.chat.completions.create(
        model="andynoodles/LLCG-OCI",
        messages=messages,
        stream=True,
    )
    
    partial_content = ""
    for chunk in stream:
        delta_content = chunk.choices[0].delta.content
        if delta_content is not None:
            partial_content += delta_content
            # Enhance LaTeX rendering for streaming content
            enhanced_content = enhance_latex_rendering(partial_content)
            yield enhanced_content

# Create the main interface with LaTeX support
with gr.Blocks(css=latex_css, title="LLCG agent", theme=gr.themes.Soft(), fill_height=True) as demo:
    # Chat interface with LaTeX support - no column wrapper needed
    chat_interface = gr.ChatInterface(
        fn=chat_stream,
        type="messages",
        title="LLCG agent",
        description="歡迎使用 LLCG agent! 我提供關於LLCG的各種資訊和幫助。請輸入您的問題或需求。",
        fill_height=True,
        # Configure LaTeX delimiters for proper rendering
        chatbot=gr.Chatbot(
            latex_delimiters=[
                {"left": "$", "right": "$", "display": False},
                {"left": "$$", "right": "$$", "display": True},
                {"left": "\\(", "right": "\\)", "display": False},
                {"left": "\\[", "right": "\\]", "display": True}
            ],
            height="70vh"
        )
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, max_threads=4, share=True)