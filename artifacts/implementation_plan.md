# Beginner-Friendly Implementation Plan: Intelligent Auditor RAG

This plan explains **how** we built the Intelligent Auditor and **why** each part is important. Think of this as the "Blueprint" for the system.

---

## 1. Project Organization (The "Skeleton")
Before writing code, we created a folder structure to keep things organized.
- **`data/raw/`**: The "In-box" where you drop your PDFs.
- **`src/`**: The "Engine Room" where all the Python logic lives.
- **`vector_store/`**: The "Memory Bank" where the AI stores what it has learned.
- **`prompts/`**: The "Rule Book" for how the AI should behave.

---

## 2. Core Components (The "Engine Parts")

### A. The Ingester (`src/ingester.py`) - *The Reader*
- **What it does**: It opens the PDFs and reads the text.
- **Why it's needed**: A computer can't "read" a PDF directly; we need this script to turn the pages into text and cut them into smaller pieces (Chunks) so the AI doesn't get overwhelmed.

### B. The Indexer (`src/indexer.py`) - *The Filing Cabinet*
- **What it does**: It takes the text chunks and turns them into "Vectors" (lists of numbers).
- **Why it's needed**: Searching for words is slow. Searching for numbers is fast. This script stores those numbers in a "Memory Bank" (FAISS) so the AI can find answers instantly.

### C. The Retriever (`src/retriever.py`) - *The Researcher*
- **What it does**: It looks through the Memory Bank to find the exact pages that match your question.
- **Why it's needed**: We use a **Hybrid** method (Keyword + Meaning) to make sure we don't miss technical terms like "Section 404" or concepts like "Financial Risk."

### D. The Generator (`src/generator.py`) - *The Writer*
- **What it does**: It takes the pages found by the Researcher and writes a human-like answer.
- **Why it's needed**: This is where the AI (GPT-4) lives. It follows strict rules to never lie, to only use the provided text, and to always cite the page numbers.

---

## 3. The Interface (The "Control Panel")

### The Main Application (`main.py`)
- **What it does**: It creates a "Server" that you can talk to.
- **Why it's needed**: It connects all the engine parts together. It provides two main buttons (endpoints):
    1. **`/ingest`**: Tell the system to start reading the files in your folder.
    2. **`/ask`**: Send a question to the Auditor and get a professional response.

---

## 4. Safety & Accuracy Rules (The "Audit Standard")
- **Grounding**: The AI is "grounded" in your documents. It isn't allowed to use general knowledge from the internet.
- **Citations**: We attach "Labels" (metadata) to every piece of text so the AI always knows exactly which page it is reading.
- **Deterministic**: We set the "Temperature" to 0 so the AI gives consistent, serious answers every time.

---

## 5. How we Verified it (The "Test Drive")
- **Smoke Test**: A quick check to see if all files and libraries are installed correctly.
- **Ingestion Test**: Running the system on real 10-K filings (Google/Tesla) to make sure it can "learn" correctly.
- **Query Test**: Asking a real question to see if the citations and facts match the actual PDF.
