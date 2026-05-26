# 🚀 Local LLM API — Built with llama.cpp + FastAPI

A lightweight, production-style **local LLM serving API** built on top of `llama.cpp` (via `llama-cpp-python`) and FastAPI.

It enables fully offline inference of quantized GGUF models with an OpenAI-like chat interface, streaming support, and a RAG-ready architecture.

---

## 🧠 What this project demonstrates

This project showcases how to build a complete **LLM inference backend system**, including:

- ⚙️ Integration of `llama.cpp` via `llama-cpp-python`
- 🚀 FastAPI-based inference server
- 💬 Multi-turn chat memory (system / user / assistant format)
- 🌊 Streaming token generation (Server-Sent Events)
- 🧩 RAG-ready context injection pipeline
- 🧠 Model-agnostic prompt engineering layer
- 🖥️ Fully local inference (no external APIs required)
- 🔌 Clean API design inspired by OpenAI chat format

---

## 🧩 Why llama.cpp

This system runs **quantized GGUF models locally** using `llama.cpp`.

### Benefits:
- Runs fully offline (no API cost)
- Efficient CPU inference
- Low memory usage via quantization
- Easy model swapping without changing API logic

---

## 📦 Project Structure

```bash
llm_api/
├── main.py              # FastAPI entrypoint
├── requirements.txt
├── .gitignore
├── models/
│   └── phi2/
│       └── phi-2.Q4_K_M.gguf   # (NOT pushed to GitHub)
└── app/
    ├── model.py        # LLM wrapper (llama-cpp-python)
    ├── prompt.py       # Prompt builder (model-agnostic)
    ├── schemas.py      # Pydantic request/response models
    └── memory.py       # Session memory (extendable to Redis)
```

---

## ⚠️ Important Note (Models are NOT included)

This repository does **NOT include model weights**.

To download the model:

```bash
mkdir -p models/phi2

huggingface-cli download TheBloke/phi-2-GGUF phi-2.Q4_K_M.gguf \
  --local-dir models/phi2
```

---

## ⚡ Features

### 💬 Chat API

* Multi-turn conversation support
* System / user / assistant roles
* Optional session-based memory (extensible)

### 🌊 Streaming

* Real-time token streaming via SSE

### 🧠 RAG Ready

* Context injection into prompts
* Compatible with FAISS / Chroma / Qdrant pipelines

### 🔁 Model Agnostic Design

Supports multiple prompt formats:

* Phi-2
* Mistral
* LLaMA-3
* ChatML

---

## 🚀 Run Locally

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📡 API Endpoints

### 🟢 Health Check

```http
GET /health
```

Response:

```json
{
  "status": "ok",
  "model": "phi-2.Q4_K_M.gguf"
}
```
---

### 💬 Chat Endpoint

```http
POST /chat
```

#### Request

```json
{
  "messages": [
    { "role": "system", "content": "You are a helpful assistant." },
    { "role": "user", "content": "Explain machine learning simply." }
  ],
  "max_tokens": 512,
  "temperature": 0.7,
  "top_p": 0.95,
  "stream": false
}
```

---

### 🧠 Chat with RAG Context

```json
{
  "messages": [
    { "role": "user", "content": "What does the document say about payments?" }
  ],
  "context": "Payment must be made within 30 days of invoice issuance.",
  "stream": false
}
```

---

### 🌊 Streaming Mode

Set:

```json
"stream": true
```

Response format (SSE):

```
data: {"choices":[{"delta":{"content":"Hello"},"finish_reason":null}]}
```

---

## 🧪 Model Information

* Model: Phi-2 (GGUF)
* Quantization: Q4_K_M
* Context length: 2048 tokens
* Backend: llama.cpp via llama-cpp-python

---

## 🧠 System Architecture

```
Client → FastAPI → Prompt Builder → llama.cpp → Token Stream → Response
                     ↑
              (RAG Context Injection)
```

---

## 🔮 Future Improvements

* Redis-based persistent memory
* Multi-model switching endpoint
* OpenAI-compatible `/v1/chat/completions`
* Docker deployment
* GPU acceleration (CUDA / Metal)
* Full RAG pipeline with vector database

---

## 🧼 Git Best Practice

This project intentionally excludes large model files.

Make sure you use:

```bash
git add .
```
ONLY after configuring `.gitignore` properly.

---

## 📜 License

MIT License

---

## 👤 Author

Built by Michel Emel  
Project: Local LLM Infrastructure using llama.cpp + FastAPI