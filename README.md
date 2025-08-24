# LLCG Web

LLCG Web is a web application that provides an interactive interface for the **LLCG-OCI** model using Gradio. This guide will help you set up and run the project locally.

The model used in this project is available on [Hugging Face](https://huggingface.co/andynoodles/LLCG-OCI).

---

## Prerequisites

* Python 3.8 or higher
* `pip` installed
* `git` (optional, for cloning the repo)

---

## Installation

1. **Create a virtual environment**

```bash
python3 -m venv .venv
```

2. **Activate the virtual environment**

* On Linux/macOS:

```bash
source .venv/bin/activate
```

* On Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

---

## Running the Application

### Step 1: Start the VLLM server

```bash
vllm serve andynoodles/LLCG-OCI
```

This will start the backend model server.

### Step 2: Launch the Gradio app

```bash
python3 gradio_app.py
```

Open the URL displayed in your terminal to access the web interface.

---

## Notes

* Make sure the VLLM server is running before starting the Gradio app.
* For more advanced configuration of the VLLM server, refer to the [VLLM documentation](https://vllm.readthedocs.io/).
