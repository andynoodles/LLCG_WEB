import gradio as gr
from openai import OpenAI
import requests
import json
import re
# Connect to local vLLM server
client = OpenAI(base_url="http://localhost:8000/v1", api_key="any_key")

# Custom CSS for better LaTeX rendering and suggestion buttons
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

/* Style for suggestion cards */
.suggestion-card {
    margin: 10px 0 !important;
    padding: 15px !important;
    border: 1px solid #e0e0e0 !important;
    border-radius: 10px !important;
    background: #fafafa !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
}

.suggestion-card:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    border-color: #007acc !important;
}

/* Dark theme support for suggestion cards */
.dark .suggestion-card {
    background: #2a2a2a !important;
    border-color: #404040 !important;
}

.dark .suggestion-card:hover {
    border-color: #4da6ff !important;
}

/* Style for clickable markdown questions */
.question-markdown {
    margin: 0 0 10px 0 !important;
    padding: 0 !important;
}

.question-markdown h3, .question-markdown h4 {
    margin-top: 0 !important;
    margin-bottom: 8px !important;
    color: #007acc !important;
}

.question-markdown code {
    background-color: rgba(0, 122, 204, 0.1) !important;
    padding: 2px 4px !important;
    border-radius: 3px !important;
}

.question-markdown pre {
    background-color: rgba(0, 122, 204, 0.05) !important;
    padding: 10px !important;
    border-radius: 5px !important;
    border-left: 3px solid #007acc !important;
}

.question-markdown ul, .question-markdown ol {
    margin: 8px 0 !important;
    padding-left: 20px !important;
}

.question-markdown p {
    margin: 5px 0 !important;
}

/* Responsive design for suggestion panel */
@media (max-width: 768px) {
    .suggestion-panel {
        display: none !important;
    }
}
</style>
"""

reform_chat_template = """<|im_start|>system
Give me a well formatted task description that matches the user's code snippet.<|im_end|>
<|im_start|>user
{prompt}<|im_end|>
<|im_start|>assistant"""

coding_chat_template = """<|im_start|>system
You are a helpful assistant.<|im_end|>
<|im_start|>user
{improved_prompt}<|im_end|>
<|im_start|>assistant"""

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
    # First stage Prompt reformulation
    reform_prompt = reform_chat_template.format(prompt=message)
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "Question_reformer_qwen:latest", "prompt": reform_prompt},
        stream=True
    )
    
    partial_content = ""
    partial_content += "# Now reforming prompt\n\n"
    yield partial_content
    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode("utf-8"))
            if "response" in data:
                partial_content += data["response"]
                #enhanced_content = enhance_latex_rendering(partial_content)
                yield partial_content
    # Second stage Code generation based on improved prompt
    partial_content += "\n\n# Now generating code based on improved prompt\n\n"
    yield partial_content
    improved_prompt = partial_content.strip()
    coding_prompt = coding_chat_template.format(
        improved_prompt=improved_prompt,
        original_prompt=message)
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "Coding_qwen:latest", "prompt": coding_prompt},
        stream=True
    )
    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode("utf-8"))
            if "response" in data:
                partial_content += data["response"]
                #enhanced_content = enhance_latex_rendering(partial_content)
                yield partial_content

    

# Sample questions for suggestions
SAMPLE_QUESTIONS = [
    """from typing import List

def has_close_elements(numbers: List[float], threshold: float) -> bool:
\"\"\" Check if in given list of numbers, are any two numbers closer to each other than
given threshold.
>>> has_close_elements([1.0, 2.0, 3.0], 0.5)
False
>>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
True
\"\"\"""",
"""from typing import List

def separate_paren_groups(paren_string: str) -> List[str]:
\"\"\" Input to this function is a string containing multiple groups of nested parentheses. Your goal is to
separate those group into separate strings and return the list of those.
Separate groups are balanced (each open brace is properly closed) and not nested within each other
Ignore any spaces in the input string.
>>> separate_paren_groups('( ) (( )) (( )( ))')
['()', '(())', '(()())']
\"\"\"""",
]

def add_sample_question(new_question):
    """Function to add new sample questions (for future enhancement)"""
    global SAMPLE_QUESTIONS
    if new_question and new_question.strip() not in SAMPLE_QUESTIONS:
        SAMPLE_QUESTIONS.append(new_question.strip())
    return SAMPLE_QUESTIONS

def use_sample_question(question):
    """Function to handle sample question selection"""
    return question

def get_question_preview(question, max_length=100):
    """Generate a short preview of the question for display"""
    # Remove markdown formatting for preview
    preview = re.sub(r'\*\*(.*?)\*\*', r'\1', question)  # Remove bold
    preview = re.sub(r'`(.*?)`', r'\1', preview)  # Remove code formatting
    preview = re.sub(r'#+\s*(.*)', r'\1', preview)  # Remove headers
    preview = re.sub(r'\n+', ' ', preview)  # Replace newlines with spaces
    preview = preview.strip()
    
    # Truncate if too long
    if len(preview) > max_length:
        preview = preview[:max_length] + "..."
    
    return preview if preview else "Click to view question"

# Create the main interface with LaTeX support
with gr.Blocks(css=latex_css, title="LLCG agent", theme=gr.themes.Soft(), fill_height=True) as demo:
    with gr.Row():
        with gr.Column(scale=3):
            # Chat interface with LaTeX support
            chat_interface = gr.ChatInterface(
                fn=chat_stream,
                type="messages",
                title="LLCG agent",
                description="歡迎使用 LLCG agent! 請輸入您的程式問題問題或需求。",
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
        
        with gr.Column(scale=1, min_width=300, elem_classes=["suggestion-panel"]):
            gr.Markdown("### 💡 建議問題")
            gr.Markdown("點擊下方問題快速開始對話：")
            
            # Create clickable cards for sample questions with markdown parsing
            for i, question in enumerate(SAMPLE_QUESTIONS):
                with gr.Group(elem_classes=["suggestion-card"]):
                    # Display the question with markdown formatting
                    question_display = gr.Markdown(
                        question,
                        elem_classes=["question-markdown"]
                    )
                    
                    # Hidden button for click functionality
                    click_btn = gr.Button(
                        f"📋 使用此問題 {i+1}",
                        variant="primary",
                        size="sm",
                        visible=True
                    )
                    
                    # Connect button to text input
                    click_btn.click(
                        fn=lambda q=question: q,
                        outputs=chat_interface.textbox
                    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, max_threads=4, share=True)

