# 🚀 Step-by-Step Deployment Guide (Render)

Since your code is on GitHub and has a `Dockerfile`, **Render** is the best way to go live for free (or very cheap).

### 1. Create a Render Account
1. Go to [render.com](https://render.com) and sign up using your **GitHub** account.

### 2. Create a New Service
1. On your Dashboard, click **New +** and select **Web Service**.
2. Connect your GitHub account and select the `intelligent-auditor-rag` repository.

### 3. Configure the Build
Render will automatically detect the `Dockerfile`. Use these settings:
- **Name**: `intelligent-auditor`
- **Region**: Select the one closest to you (e.g., Oregon or Singapore).
- **Environment**: **Docker** (it should pick this automatically).

### 4. Add Secret Keys (CRITICAL)
Your app will crash if it doesn't have your API keys.
1. Click the **Advanced** button.
2. Add an **Environment Variable**:
   - **Key**: `OPENAI_API_KEY`
   - **Value**: `your_actual_openai_api_key_here`
3. (Optional) Add `LANGCHAIN_API_KEY` if you want tracing.

### 5. Deploy!
1. Click **Create Web Service**.
2. Wait 2-3 minutes. You will see a log saying `Application startup complete`.
3. Render will give you a URL like `https://intelligent-auditor.onrender.com`.

---

### 🎙️ How to confirm it's live:
Once the URL is ready, add `/docs` at the end (e.g., `https://...onrender.com/docs`). 
If you see the **FastAPI Swagger UI**, your "Intelligent Auditor" is officially live on the internet!

### ⚠️ Pro Tip for Interview:
If the interviewer asks about costs, tell them: 
*"I'm using a **Serverless Container** model. It only charges based on usage, so it's extremely cost-effective for an auditing tool that isn't running 24/7."*
