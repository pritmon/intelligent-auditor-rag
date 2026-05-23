# PRO TIP: This is a Dockerfile. It is a "Recipe" to build a consistent computer for your app.

# 1. Base Image: Use a lightweight version of Python 3.11.
FROM python:3.11-slim

# 2. Environment Setup: Prevents Python from creating messy cache files (.pyc).
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# CRIT-4: KMP_DUPLICATE_LIB_OK removed — fix the root cause (conflicting OpenMP libs)
# by ensuring only one OpenMP runtime is present via proper dependency pinning.

# 3. Work Directory: Every command after this runs inside the "/app" folder.
WORKDIR /app

# 4. System Tools: Install low-level libraries needed for FAISS and high-performance search.
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 5. Dependencies: Copy requirements first to speed up future builds (caching).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Source Code: Copy all your project files into the container.
COPY . .

# 7. Safety: Ensure all required folders exist.
RUN mkdir -p data/raw data/processed vector_store artifacts

# 8. Communication: Tell the container to listen on port 8000.
EXPOSE 8000

# 9. Startup: The command that runs when the container starts.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
