# LiveKit LangGraph Voice Assistant

This project implements a real-time voice AI assistant using the **LiveKit agents framework** integration with **LangGraph**. It combines state-of-the-art Speech-to-Text (STT), Text-to-Speech (TTS), and Voice Activity Detection (VAD) to create a conversational interface that delegates logic and retrieval tasks to a LangGraph workflow.

## Table of Contents

* [🤖 Overview](#-overview)
* [✨ Features](#-features)
* [🧰 Tech Stack](#-tech-stack)
* [🧠 Architecture](#-architecture)
* [🔁 LangGraph Flow](#-langgraph-flow)
* [📚 Knowledge Base & Retrieval Tools](#-knowledge-base--retrieval-tools)
* [🎥 Demo](#-demo)
* [🚀 Getting Started](#-getting-started)
    * [✅ Prerequisites](#-prerequisites)
    * [📦 Installation](#-installation)
    * [▶️ Run the App](#-run-the-app)
    * [⚙️ Configuration (UI / ENV / CLI)](#-configuration-ui--env--cli)
* [🔎 How It Works (Step-by-Step)](#-how-it-works-step-by-step)
* [🛠️ Customization](#-customization)
* [🧯 Troubleshooting](#-troubleshooting)
* [⚠️ Known Limitations](#-known-limitations)
* [🔐 Security Notes](#-security-notes)
* [🗺️ Roadmap Ideas](#-roadmap-ideas)
* [🙏 Acknowledgements / Sources](#-acknowledgements--sources)
* [📄 License](#-license)
* [📁 Project Structure](#-project-structure)

---

## 🤖 Overview

This repository contains the source code for a voice agent (`agent.py`) that acts as a real-time interface. Instead of a static LLM, the agent connects to a dynamic workflow defined in `graph.py`. This allows for complex behaviors such as **RAG (Retrieval Augmented Generation)**, tool usage, or multi-step reasoning, while maintaining low-latency voice interaction.

## ✨ Features

* **Real-time Voice Interaction**: Full-duplex conversational capabilities.
* **LangGraph Integration**: Uses `LLMAdapter` to bridge LiveKit's voice pipeline with LangGraph workflows.
* **Advanced Audio Processing**:
    * **STT**: Streaming transcription via AssemblyAI.
    * **TTS**: High-quality voice synthesis via Cartesia (Sonic-3 model).
    * **VAD**: Silero VAD for precise endpointing.
    * **Noise Cancellation**: Automatic background noise suppression.
* **Multilingual Support**: Includes a multilingual turn detection model.
* **Custom Personality**: Configured as a helpful, humorous, and concise assistant.

## 🧰 Tech Stack

| Component | Technology |
| :--- | :--- |
| **Language** | Python |
| **Real-Time Transport** | LiveKit |
| **Orchestration** | LangGraph / LangChain |
| **Speech-to-Text (STT)** | AssemblyAI (universal-streaming:en) |
| **Text-to-Speech (TTS)** | Cartesia (sonic-3) |
| **Voice Activity Detection (VAD)** | Silero |
| **Environment Management** | python-dotenv |

## 🧠 Architecture

The application runs as a LiveKit Agent plugged into a Room.

1. **Audio Input**: User speaks; audio is cleaned via Noise Cancellation.
2. **Transcription**: AssemblyAI converts speech to text.
3. **Reasoning**: The `LLMAdapter` forwards the transcript to the LangGraph workflow (`create_workflow()`).
4. **Generation**: The graph processes the input (potentially retrieving data) and returns text.
5. **Audio Output**: Cartesia converts the text response to audio.

## 🔁 LangGraph Flow

The agent logic is decoupled from the voice transport.

* **Initialization**: The workflow is instantiated via `create_workflow()` imported from `graph.py`.
* **Adapter**: The `livekit.plugins.langchain.LLMAdapter` wraps the graph, allowing the LiveKit `AgentSession` to treat the complex graph as a standard LLM interface.
* **Workflow Details**: *Note: The specific nodes and edges are defined in `graph.py` (not included in the provided snippet), but the architecture supports cyclical graphs, tool calling, and state management.*

## 📚 Knowledge Base & Retrieval Tools

The retrieval logic is encapsulated within the `Rag_Workflow`.

* **Integration Point**: The `agent.py` file initializes the RAG workflow but does not directly configure vector stores or embeddings.
* **Implementation**: Refer to `graph.py` for specific details on:
    * Vector Databases (e.g., Pinecone, Chroma)
    * Embeddings Models
    * Search Tools

## 🎥 Demo

https://drive.google.com/drive/folders/1WYS-zAnQV4M2VaEw2I0PiJeujfYSAEiL?usp=drive_link

## 🚀 Getting Started

### ✅ Prerequisites

* Python 3.9+
* LiveKit Cloud project or local LiveKit server.
* API Keys for:
    * LiveKit (URL, API Key, Secret)
    * AssemblyAI
    * Cartesia
    * OpenAI/Anthropic (depending on the LLM backend used in `graph.py`)

### 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone <repository_url>
   cd <project_directory>
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   *(Based on imports)*
   ```bash
   pip install livekit-agents livekit-plugins-assemblyai livekit-plugins-cartesia livekit-plugins-silero livekit-plugins-langchain langchain langgraph python-dotenv
   ```

### ▶️ Run the App

1. **Start the agent in development mode**:
   ```bash
   python agent.py dev
   ```

2. **Connect to the agent** using the LiveKit Playground or a compatible frontend client.

### ⚙️ Configuration (UI / ENV / CLI)

Create a `.env.local` file in the root directory:

```ini
LIVEKIT_URL=wss://...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
ASSEMBLYAI_API_KEY=...
CARTESIA_API_KEY=...
OPENAI_API_KEY=... # Or other LLM provider keys
```

## 🔎 How It Works (Step-by-Step)

1. **Startup**: `agents.cli.run_app(server)` starts the worker.
2. **Connection**: When a room session initiates (`@server.rtc_session`), `my_agent` is called.
3. **Graph Setup**: `create_workflow()` builds the LangGraph executable.
4. **Session Config**: An `AgentSession` is configured with specific plugins (AssemblyAI, Cartesia, Silero).
5. **Room Entry**: The bot enters the room with noise cancellation enabled.
6. **Interaction**: The bot sends an initial instruction "Greet the user..." to the graph to kickoff conversation.

## 🛠️ Customization

* **System Prompt**: Modify the `instructions` argument in the `Assistant` class in `agent.py`.
  ```python
  instructions="You are a helpful voice AI assistant..."
  ```

* **Voice Model**: Change the Cartesia voice ID in the `tts` configuration.
  ```python
  tts="cartesia/sonic-3:<NEW_VOICE_ID>"
  ```

* **Logic**: Edit `graph.py` to change how the bot thinks, retrieves information, or uses tools.

## 🧯 Troubleshooting

* **Agent disconnects immediately**: Check `LIVEKIT_URL` and keys in `.env.local`.
* **No Audio/Voice**: Verify AssemblyAI and Cartesia API credits/keys.
* **Latency/Lag**: Ensure the server running the agent has a stable internet connection. WebRTC is sensitive to network jitter.

## ⚠️ Known Limitations

* The instruction set in `agent.py` strictly forces no emojis/formatting ("concise, to the point... no complex formatting"). This is optimized for TTS reading.
* Depends on external cloud APIs (AssemblyAI, Cartesia); service outages will affect the agent.

## 🔐 Security Notes

* **Environment Variables**: Never commit `.env.local` to version control.
* **Participant Data**: The agent has access to raw audio streams in the room. Ensure compliance with local recording laws.

## 🗺️ Roadmap Ideas

* Implement local STT (Whisper) for reduced cost.
* Add specific tools inside `graph.py` (Calendar, Weather, etc.).
* Add support for interruption handling (user interrupts the bot).

## 🙏 Acknowledgements / Sources

* [LiveKit Agents Framework](https://github.com/livekit/agents)
* [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)

## 📄 License

Project License information is currently not specified.

## 📁 Project Structure

```text
├── agent.py            # Main entry point and LiveKit Agent configuration
├── graph.py            # (Implied) Contains create_workflow() and LangGraph logic
├── .env.local          # Environment configuration (Keys/Secrets)
└── requirements.txt    # (Implied) Python dependencies
```
