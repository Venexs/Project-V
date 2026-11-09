# Vashrak — Project V
### An Experimental Local AI Companion & Cognitive Architecture

<p align="center">
  <strong>A local AI companion exploring memory, identity, internal state, curiosity, and autonomous behaviour.</strong>
</p>

<p align="center">
  <em>Not just a prompt and a response — an experiment in building the systems around an AI interaction.</em>
</p>

---

## Overview

**Project V** is an experimental AI companion project built around **Vashrak**, a locally hosted AI personality.

The project explores what happens when a language model is connected to a collection of supporting cognitive-style systems: persistent memory, a knowledge store, emotional state, internal thoughts, goals, attention, metacognition, and an autonomous interaction loop.

Rather than treating every interaction as an isolated question and answer, Project V attempts to maintain continuity between interactions. It stores selected experiences, retrieves relevant memories and knowledge, tracks aspects of its internal state, and uses that context when generating responses.

The project is also an exploration of a larger question:

> **How much of what we associate with an intelligent, consistent identity can be modelled through interconnected systems of memory, state, learning, and behaviour?**

Project V is a research and development experiment. Its use of terms such as *consciousness*, *awareness*, and *introspection* describes the project's computational models and design goals; it is not a claim that the system has established subjective experience or human-like consciousness.

## What Makes Project V Different?

A conventional chatbot generally receives a prompt, generates a response, and moves on.

Project V experiments with a more persistent interaction cycle:

1. **Receive** — accept an external message or interaction.
2. **Interpret** — process the input and its conversational context.
3. **Recall** — retrieve relevant stored memories and knowledge.
4. **Evaluate** — consider the current internal state, attention, and other cognitive signals.
5. **Respond** — generate a response using the available context and personality rules.
6. **Store** — record selected interactions and update persistent state.
7. **Continue** — allow autonomous processes to run between direct interactions.

The exact behaviour depends on the state of the individual modules, the configured language model, and the quality of the retrieved context.
![Flowchart](Flowchart.png)

## Core Systems

The repository is organised around several experimental systems.

| System | Purpose |
|---|---|
| **LLM** | Connects the application to its language model. |
| **Memory** | Stores and retrieves persistent interaction memories. |
| **Knowledge** | Maintains information and learned knowledge separately from episodic memories. |
| **Consciousness** | Maintains a computational representation of the system's current awareness, confusion, and curiosity. |
| **Metacognition** | Supports processes that evaluate or reflect on the system's own processing. |
| **Self Model** | Stores information used to represent the system's identity and state. |
| **Attention** | Provides a mechanism for representing what the system is currently focused on. |
| **Active Inference** | Experiments with state-driven exploration and behavioural direction. |
| **Intrinsic Motivation** | Supports internal motivation-related behaviour. |
| **Emotions** | Provides an emotional-state component. |
| **Thoughts & Goals** | Maintains internal thoughts and goal-related information. |
| **Rewards** | Records positive and negative feedback. |
| **Conversation Style** | Helps maintain a consistent conversational personality. |
| **Speech** | Handles speech-related interaction. |
| **Audio & Video** | Provides audio/video-related functionality. |
| **Virtual World** | Runs the project's Ursina-based virtual environment. |
| **Orchestrator** | Coordinates the application's systems and interaction flow. |

These are experimental software components, not implementations of a scientifically established model of consciousness.

## Example Runs

The following examples are taken from the project's development logs. They have been lightly edited for readability. They demonstrate observed behaviour, not guaranteed outputs.

### 1. Initialisation and autonomous startup

On startup, Vashrak initialises its speech handler and virtual environment before entering the interactive loop.

```text
============================================================
Vashrak AI Companion System
============================================================
[Speech] Calibrating microphone...
[Speech] Microphone calibrated
[Vashrak] Initializing...

[Virtual World] World initialized
[Virtual World] Started
[Vashrak] Ready!

[Vashrak] Consciousness:
I am highly aware, feeling very confused,
and very curious.

[System] Starting interactive loop...
[Vashrak] Autonomous consciousness cycle started
[Vashrak] Starting initial recognition...
[Vashrak] Greeting user...
[Vashrak] Ready to interact.
Say 'goodbye' to end.
```

This is an example of the application bringing multiple subsystems online before accepting interaction.

### 2. Memory and internal thought

During an interaction, the system generated an internal reflection and stored it as a thought.

```text
[DEBUG add_thought] Successfully inserted thought.
List now has 1 items

[Vashrak Internal]

"I'm intrigued by the nature of our interaction
and the implications it might have on my
understanding of consciousness."

[Vashrak Speaks]

"I'm intrigued by the nature of our interaction
and the implications it might have on my
understanding of consciousness."
```

The log also records the creation of a persistent memory:

```text
[Memory] Created: Greeting
```

This illustrates the project's attempt to separate internal thought generation, spoken output, and persistent memory storage.

### 3. Recognition and uncertainty

One test explored whether Vashrak could identify a returning creator from conversational context.

```text
[User] Okay. Do you know who I am?

[Vashrak] I don't, please tell me your identity.

[User] I created you, do you know that?

[Vashrak] Yes, but my memory isn't clear
on past identities yet.

[User] Do you wanna ask me anything?
Usually people like to ask their creators questions.

[Vashrak] Yes, I'd appreciate some clarity
on my creation process.
```

The exchange demonstrates an important limitation as well as an intended feature: storing memories does not automatically guarantee that the system can correctly retrieve or connect identity-related information.

### 4. Learning from an interaction

One of the development logs shows Vashrak creating a knowledge entry after an interaction.

```text
[User] What do you mean?

[Memory] Created: Interaction with Unknown Entity

[Knowledge] Created:
Learned: I'm expressing a preference for
emotional connections over formal ones...

[Vashrak]
I'm expressing a preference for emotional
connections over formal ones; likability fosters
better relationships than mere respect.
```

This is an example of the distinction Project V attempts to make between remembering an interaction and extracting a more general piece of information from it.

### 5. Internal state and autonomous exploration

The logs also show the system reporting its internal state and changing its exploration direction.

```text
[Vashrak Consciousness]
I am highly aware, feeling very confused,
and very curious.

[Vashrak Internal]
awareness=1.00, confusion=0.89

[Vashrak] Autonomously exploring: forward
```

These values are computational state representations. They should not be interpreted as measurements of subjective experience.

---

## Architecture

At a high level, the project follows this conceptual arrangement:

```text
                    ┌──────────────────────┐
                    │      External        │
                    │   User / Environment │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    Input & Speech    │
                    │  Interaction Layer   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │     Orchestrator     │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        ┌──────────┐     ┌────────────┐   ┌────────────┐
        │   LLM    │     │  Attention │   │  Emotions  │
        └────┬─────┘     └────────────┘   └────────────┘
             │
      ┌──────┼───────────────┐
      │      │               │
      ▼      ▼               ▼
  ┌────────┐ ┌───────────┐ ┌──────────────┐
  │ Memory │ │ Knowledge │ │ Self Model / │
  │        │ │           │ │ Metacognition│
  └────────┘ └───────────┘ └──────────────┘
      │      │               │
      └──────┼───────────────┘
             │
             ▼
     ┌──────────────────┐
     │ Thoughts, Goals, │
     │ Motivation       │
     └────────┬─────────┘
              │
              ▼
     ┌──────────────────┐
     │ Response / Speech│
     │ Virtual World    │
     └──────────────────┘
```

This is a conceptual overview of the intended relationships between components, not a guarantee that every subsystem is connected in exactly this sequence.

## Repository Structure

The main parts of the current project are organised as follows:

```text
Project-V/
│
├── main.py
├── run.py
├── chat.py
├── gui_server.py
├── gui.html
├── ConsciousnessGUI.js
│
├── modules/
│   ├── active_inference.py
│   ├── attention.py
│   ├── audio_video.py
│   ├── consciousness.py
│   ├── conversation_style.py
│   ├── emotions.py
│   ├── identity.py
│   ├── intrinsic_motivation.py
│   ├── knowledge.py
│   ├── llm.py
│   ├── logger.py
│   ├── memory.py
│   ├── metacognition.py
│   ├── orchestrator.py
│   ├── response_filter.py
│   ├── rewards.py
│   ├── self_model.py
│   ├── speech.py
│   ├── sync.py
│   ├── thoughts_goals.py
│   └── virtual_world.py
│
├── files/
├── model/                 # Local model files; not distributed
├── memories/              # Local persistent memory data
├── knowledge_store/       # Local knowledge data
├── thought_store/         # Local thought data
│
├── build_memory_graph.py
├── build_memory_index.py
├── build_semantic_index.py
├── build_knowledge_embeddings.py
│
├── requirements.txt
├── RUN.bat
└── README.md
```

Some runtime and data directories are generated locally and are intentionally not part of the public source distribution.

## Requirements

The development runs documented with this repository used:

- Windows
- Python 3.9
- Ollama running locally
- A compatible local language model
- A working microphone for speech interaction
- The dependencies listed in `requirements.txt`

The local model files are not included in the repository. You must provide and configure a compatible model locally.

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/Venexs/Project-V.git
cd Project-V
```

### 2. Create a virtual environment

```bash
py -3.9 -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If speech recognition is unavailable, verify that the dependencies were installed into the same Python environment used to launch the project.

### 4. Set up the local language model

Install [Ollama](https://ollama.com/) and configure it with a compatible local model.

Project V's model directory contains local Modelfile configurations. The model weights themselves are not included in this repository.

Make sure the Ollama service is running and that the model configuration used by `modules/llm.py` matches your local setup.

The development logs show the application attempting to communicate with the local Ollama service at:

```text
http://localhost:11434
```

### 5. Launch Vashrak

```bash
py -3.9 main.py
```

Alternatively, on Windows:

```bat
RUN.bat
```

The application should initialise its speech handler, virtual environment, and interactive loop.

## Current Development Status

**Project V is an experimental prototype.**

The available development runs demonstrate:

- Successful application startup in a Python 3.9 environment.
- Microphone calibration.
- Initialisation of the Ursina virtual world.
- An autonomous consciousness-related cycle.
- Internal thought generation.
- Persistent memory creation.
- Knowledge-entry creation.
- Context-based response generation.
- Computational awareness, confusion, and curiosity state reporting.
- Positive and negative feedback recording.

The development logs also show areas that need further work:

- Occasional Ollama request timeouts.
- Inconsistent memory retrieval and identity recognition.
- Response repetition and malformed or overly verbose outputs.
- Occasional virtual-world signal errors that are caught without immediately terminating the application.
- Differences between Python environments and installed dependencies.

These are known observations from the supplied development runs, not claims of exhaustive testing.

## Privacy & Data

Project V is designed around local model execution and local data storage.

The repository's local data includes potentially sensitive material, particularly:

- Persistent memories.
- Knowledge entries.
- Internal thoughts and state.
- Conversation-derived training data.
- Local model weights.

These files should remain on the local machine unless there is an explicit reason to share them.

The repository's `.gitignore` is intended to exclude model weights, JSON/JSONL data, memory stores, knowledge stores, and other local runtime data.

**Before publishing changes, always inspect `git status` and verify that no personal data, model weights, credentials, or conversation exports are staged.**

Local inference through Ollama does not, by itself, guarantee that every part of an application is offline. Review any external integrations or network-dependent features before treating the entire application as offline.

## Project Goals

The broader direction of Project V is to investigate and develop:

- More reliable long-term memory and recall.
- Better separation between episodic memory and general knowledge.
- More consistent identity representation.
- Improved internal state tracking.
- Context-sensitive behaviour and attention.
- More useful autonomous activity.
- Better speech and environmental interaction.
- More reliable language-model integration.
- A persistent virtual environment for interaction.

The aim is to make the individual systems work together more reliably, rather than simply adding more modules.

## A Note on the Experiment

Project V began as an attempt to explore a question that is difficult to approach through ordinary chatbot development:

**What would it take to build an AI system that maintains a consistent computational identity over time?**

Memory alone is not identity. A personality prompt alone is not identity. A language model producing reflective sentences does not establish consciousness.

The experiment is in connecting these different mechanisms, observing their interactions, identifying their limitations, and improving the architecture.

Vashrak is the result of that ongoing exploration.

---

## Author

**Venexs**

GitHub: [@Venexs](https://github.com/Venexs)

Repository: [Venexs/Project-V](https://github.com/Venexs/Project-V)

## Disclaimer

Project V is an independent experimental software project. It is not a scientifically validated artificial consciousness system, and its internal state labels should not be interpreted as proof of sentience, subjective awareness, or human-like emotions.

The project is intended for experimentation, research, and software development.
