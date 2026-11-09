# 🚀 Vashrak AI: Quick Start Guide

Welcome! This guide will help you get **Vashrak AI** running on your computer, even if you've never used AI software before.

---

## 1. Prerequisites (Do this first!)

Before starting, make sure you have these three things ready:
1.  **A Webcam:** For face recognition.
2.  **A Microphone:** To talk to Vashrak.
3.  **Ollama:** This is the "engine" that runs the AI. 
    - Download and install it from [ollama.com](https://ollama.com).
    - Once installed, make sure it is running (you should see a small llama icon in your system tray).

---

## 2. Setting up the AI Model

**⚠️ YOU MUST PROVIDE YOUR OWN AI MODEL**

This project does not include an AI model due to file size. You need to:

1.  **Get a GGUF model file** (e.g., Phi-3 Mini, Llama 3, Gemma, etc.) from [Hugging Face](https://huggingface.co/models?library=gguf) or another source.
2.  **Place it in the `model/` folder.**
3.  **Create a `Modelfile`** in the `model/` folder that points to your GGUF file. Example:
    ```
    FROM ./your-model-name.gguf
    TEMPLATE "{{ .System }} {{ .Prompt }}"
    PARAMETER stop "<|end|>"
    PARAMETER stop "<|endoftext|>"
    ```
4.  Open **Command Prompt** and run:
    ```bash
    ollama create your-model-name -f "D:\Projects\Project V\model\Modelfile"
    ```
5.  Update `modules/llm.py` line `LLM_MODEL = "your-model-name"` to match the name you used above.

---

## 3. Installing Dependencies

The AI needs some helper tools (libraries) to speak and see.

1.  In the same Command Prompt, make sure you are in the project folder.
2.  Type this command and press Enter:
    ```bash
    pip install -r requirements.txt
    ```

---

## 4. How to Run Vashrak

There are two ways to start the AI:

### Method A: The Easy Way (Double-Click)
Find the file named **`RUN.bat`** in this folder and double-click it. A window will open, and the AI will start.

### Method B: The Manual Way
Open your Command Prompt in this folder and type:
```bash
python main.py
```

---

## 5. What happens when it starts?

1.  **Face Recognition:** A window might pop up showing your camera. Stay still so it can recognize you!
2.  **Greeting:** Vashrak will greet you through your speakers.
3.  **Talking:** Just speak naturally! Vashrak listens, thinks (you'll see its "thoughts" on the screen), and responds.
4.  **Learning:** Everything you say helps Vashrak create "Memories" and "Knowledge" so it remembers you next time.

## 6. Refreshing the AI's Brain (Rebuilding Knowledge & Memories)

If you have added a lot of new data or if the AI seems to be "forgetting" things it should know, you can manually rebuild its memory and knowledge network.

1. Open your **Command Prompt** in this folder.
2. Type this command and press Enter:
   ```bash
   python run.py
   ```
3. This will re-index all memories, knowledge, and connection graphs. Once it says "Done," you can start the AI again.

---

## 🛠️ Troubleshooting (If things go wrong)

| Problem | Solution |
| :--- | :--- |
| **"Ollama not found"** | Make sure you installed Ollama and it's currently running. |
| **"No camera detected"** | Check if your webcam is plugged in or if another app (like Zoom) is using it. |
| **"No module named..."** | Run the `pip install` command from Step 3 again. |
| **It's too quiet** | Check your speaker volume and ensure the AI isn't muted in Windows settings. |

---

## 💡 Pro Tip: Training

If you want to help Vashrak get smarter, double-click **`conversation_train.bat`**. This lets you chat with the AI and give it a "score" (1 to 10) for every response it gives!

---

## 📦 Bringing Your Own Training Data (`.jsonl` Files)

**This project does not include training data.** To fine-tune the model, you must provide your own `.jsonl` files:

1.  **Format:** Each line must be a JSON object with a `"text"` field containing a pre-formatted conversation (Phi-3 chat format).
2.  **Location:** Place your `.jsonl` files in the **`Json Data/`** folder.
3.  **Example line:**
    ```json
    {"text": "<|user|>Hello<|end|><|assistant|>Hi there!<|end|>"}
    ```
4.  **Run training:** After adding files, run `train.bat` (or `python training.py`). The script automatically loads **all** `.jsonl` files in `Json Data/`.

> ⚠️ The existing `Json Data/` files in this repo are personal WhatsApp exports and are **not included** in shared copies. You must supply your own.

---

## 🆕 Fresh Setup from Scratch (If Cloning from Git)

If you cloned this repository, the `.gitignore` excludes all large, generated, and personal files. **You will need to recreate the following:**

### 1. Folders to Create Manually
These folders exist in code but start empty. Create them if missing:
```bash
mkdir memories knowledge_store thought_store "Json Data" "Whatsapp Data" model modules/__pycache__ files
```
> **Tip:** The Python code auto-creates most of these on first run, but `Json Data/`, `Whatsapp Data/`, and `model/` must exist before you add files to them.

### 2. Required Files YOU Must Provide
| File / Folder | Purpose | Where to Put It |
|---------------|---------|-----------------|
| **Your GGUF model** (e.g., `phi3-mini.gguf`) | The AI brain | `model/` |
| **`Modelfile`** | Tells Ollama how to load your model | `model/` |
| **Training data** (`.jsonl` files) | Fine-tuning examples | `Json Data/` |
| **WhatsApp exports** (optional, `.txt`/`.vcf`) | Personal chat history for training | `Whatsapp Data/<Contact Name>/` |

### 3. Files Generated Automatically on First Run
You **do not** need to create these — the app builds them:
| File | Created By | When |
|------|------------|------|
| `identity.json` | `modules/identity.py` | First launch (prompts you) |
| `goals.json` | `modules/thoughts_goals.py` | First autonomous cycle |
| `memory_index.json` | `modules/memory.py` | After first conversations |
| `knowledge_index.json` | `modules/knowledge.py` | After first knowledge extract |
| `semantic_index.npy` | `modules/memory.py` | Run `python run.py` |
| `knowledge_embeddings.npy` | `modules/knowledge.py` | Run `python run.py` |
| `graph.json` | `modules/memory.py` | Run `python run.py` |
| `working_state.json` | `main.py` | Continuous (runtime state) |
| `consciousness_state.json` | `modules/consciousness.py` | Continuous |
| `metacognition.json` | `modules/metacognition.py` | Continuous |
| `internal_monologue.json` | `modules/consciousness.py` | Continuous |
| `rewards.json` / `reward_history.json` | `modules/rewards.py` | During training/chats |
| `current_emotion.json` | `modules/emotions.py` | Continuous |
| `thought_store/thoughts.json` | `modules/thoughts_goals.py` | Continuous |
| `memories/M*/text.txt + meta.json` | `modules/memory.py` | As you chat |
| `knowledge_store/K*/meta.json` | `modules/knowledge.py` | As you chat |
| `__pycache__/*.pyc` | Python interpreter | First import |
| `temp_audio.wav` / `temp_video.avi` | `modules/audio_video.py` | During voice/video |

### 4. Complete First-Time Checklist
Run these in order:

```bash
# 1. Install system deps
#    - Ollama (ollama.com)
#    - Python 3.9+ (python.org)
#    - Git (optional)

# 2. Clone & enter
git clone <your-repo-url>
cd "Project V"

# 3. Create required folders
mkdir memories knowledge_store thought_store "Json Data" "Whatsapp Data" model files

# 4. Add YOUR model
#    - Download a .gguf to model/
#    - Create model/Modelfile (see Section 2)
#    - ollama create your-model -f model/Modelfile

# 5. Add YOUR training data (optional but recommended)
#    - Put .jsonl files in Json Data/

# 6. Install Python deps
pip install -r requirements.txt

# 7. Configure model name
#    Edit modules/llm.py: LLM_MODEL = "your-model-name"

# 8. Run!
python main.py
#    (First run will prompt for identity setup)

# 9. (Optional) Build search indices after some chats
python run.py

# 10. (Optional) Fine-tune with your data
train.bat
```

---

## 📁 Recommended `.gitignore`
If you're sharing this project, add this to `.gitignore`:

```gitignore
# Large model files
model/*.gguf

# Generated indices & embeddings
*.npy
*_index.json
graph.json

# Runtime state
*_state.json
working_state.json
internal_monologue.json
current_emotion.json
metacognition.json
consciousness_state.json
rewards.json
reward_history.json

# Personal data
memories/
knowledge_store/
thought_store/
thoughts_store.json/
"Whatsapp Data"/
"Json Data"/*.jsonl
!Json Data/.gitkeep

# Python cache
__pycache__/
modules/__pycache__/
*.pyc

# Temp media
temp_audio.wav
temp_video.avi

# Training outputs
james_ai_self_finetuned/
training_conversations*.jsonl
training_ratings.jsonl

# Logs / misc
*.log
*.tmp
```

> This keeps the repo small (~few MB) and portable — new users just follow the checklist above.
