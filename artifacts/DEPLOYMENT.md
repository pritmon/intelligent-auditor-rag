# 🚀 Intelligent Auditor RAG — Deployment Guide (Render)

---

## 🗂️ Quick Navigation

| Colour | Section | Steps |
|:---:|---|:---:|
| 🔵 | [Pre-Deployment Checklist](#-pre-deployment-checklist) | S1 – S6 |
| 🟢 | [Render Setup — Step by Step](#-render-setup--step-by-step) | S7 – S12 |
| 🟠 | [Environment Variables](#-environment-variables) | S13 – S15 |
| 🟣 | [Common Failures & Fixes](#-common-failures--fixes) | S16 – S20 |
| 🔷 | [Post-Deployment Verification](#-post-deployment-verification) | S21 – S23 |
| 🔴 | [Monitoring & Cost Management](#-monitoring--cost-management) | S24 – S26 |

---

## 🔵 Pre-Deployment Checklist

> 💡 **Think of this like a pilot's pre-flight checklist. Skip one item and the plane doesn't take off.**

---

### 🔵 S1 — Check your `requirements.txt` is clean

Every library your app needs must be listed. Every library that is NOT needed must be removed.

| Check | Why it matters |
|---|---|
| No unused libraries | `sentence-transformers` caused an OOM crash (200MB unused) |
| Versions pinned with upper bounds | Prevents surprise breaking changes on redeploy |
| `faiss-cpu` not `faiss-gpu` | Render free tier has no GPU |

```
# ✅ Good
faiss-cpu>=1.7.0,<2.0.0
openai>=1.0.0,<2.0.0

# ❌ Bad — unpinned, installs latest, may break
faiss-cpu
openai
```

---

### 🔵 S2 — Confirm your `Procfile` exists and reads `$PORT`

Render assigns your app a port via the `PORT` environment variable. If you hardcode a port, Render can't find your app and kills the deploy.

```
# ✅ Correct Procfile
web: uvicorn main:app --host 0.0.0.0 --port $PORT

# ❌ Wrong — hardcoded port, Render will say "No open ports detected"
web: uvicorn main:app --host 0.0.0.0 --port 8000
```

Also check `main.py` fallback:
```python
# ✅ Correct
uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
```

---

### 🔵 S3 — Check `.gitignore` is NOT blocking data files

Common mistake: `.gitignore` blocks your PDF and vector index from reaching Render.

```bash
# ❌ These lines in .gitignore will break the live demo
data/raw/*
vector_store/*

# ✅ Remove those lines so Tesla.pdf and FAISS index reach Render
```

Verify the files are tracked:
```bash
git ls-files data/raw/
git ls-files vector_store/
# Both should list files. If empty — they are gitignored.
```

---

### 🔵 S4 — Confirm your `.env` is in `.gitignore`

Your API keys must NEVER go to GitHub.

```bash
# .gitignore must contain:
.env

# Verify:
git status
# .env must NOT appear as a tracked file
```

---

### 🔵 S5 — Check `artifacts/` directory is created at startup

Render's filesystem is ephemeral. If your code writes logs to `artifacts/`, create the folder in code — not just locally.

```python
# main.py — must exist before FileHandler is created
os.makedirs("artifacts", exist_ok=True)
```

---

### 🔵 S6 — Run locally one final time before pushing

```bash
# Fresh install — simulate what Render will do
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# Test the endpoint
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Tesla total revenue?"}'
```

If this works locally — deploy. If not — fix first.

---

## 🟢 Render Setup — Step by Step

> 💡 **Render is like a landlord for your app. You give it your code, it gives you a live URL.**

---

### 🟢 S7 — Create a Render Account

1. Go to [render.com](https://render.com)
2. Sign up using your **GitHub** account
3. Authorize Render to access your repositories

---

### 🟢 S8 — Create a New Web Service

1. Click **New +** → **Web Service**
2. Select **Build and deploy from a Git repository**
3. Connect your GitHub account if not already connected
4. Select `intelligent-auditor-rag` repository
5. Click **Connect**

---

### 🟢 S9 — Configure the Service

| Setting | Value | Why |
|---|---|---|
| **Name** | `intelligent-auditor` | Becomes part of your URL |
| **Region** | Oregon (US West) or Singapore | Choose closest to you |
| **Branch** | `main` | Auto-deploys on every push |
| **Runtime** | Python 3 | Detected from repo |
| **Build Command** | `pip install -r requirements.txt` | Installs dependencies |
| **Start Command** | Leave blank — Procfile handles it | Procfile overrides this |

---

### 🟢 S10 — Select the Instance Type

| Tier | RAM | Cost | Suitable for |
|---|---|---|---|
| **Free** | 512 MB | $0/month | Demo and testing |
| **Starter** | 512 MB | $7/month | Always-on, no cold starts |
| **Standard** | 2 GB | $25/month | Production with real users |

> ⚠️ **Free tier warning:** Free tier spins down after 15 minutes of inactivity. First request after sleep takes 30–60 seconds (cold start). Add a cold start message in your UI so users don't think it's broken.

> ⚠️ **OOM warning:** Free tier has 512 MB RAM. Do NOT add heavy libraries like `sentence-transformers` (~200MB) unless you actually use them.

---

### 🟢 S11 — Add Environment Variables (before deploying)

Click **Advanced** → **Add Environment Variable**

| Key | Value | Required |
|---|---|---|
| `OPENAI_API_KEY` | `sk-your-key-here` | ✅ Yes — app crashes without it |
| `LLM_MODEL` | `gpt-4o-mini` | Optional — defaults to gpt-4o-mini |
| `LANGCHAIN_API_KEY` | `ls-your-key-here` | Optional — for LangSmith tracing |
| `LANGCHAIN_TRACING_V2` | `true` | Optional — enables tracing |
| `AUDITOR_API_KEY` | `any-secret-string` | Optional — locks the API |

> ⚠️ Never paste API keys into `main.py` or `requirements.txt`. Environment variables in Render dashboard are encrypted.

---

### 🟢 S12 — Deploy

1. Click **Create Web Service**
2. Render starts the build — watch the log stream
3. Look for: `Application startup complete` ✅
4. Your URL will be: `https://intelligent-auditor.onrender.com`

**Expected build time:** 3–5 minutes on first deploy.

---

## 🟠 Environment Variables

> 💡 **Environment variables are like secret notes passed to your app at startup — they never appear in your code or GitHub.**

---

### 🟠 S13 — What each variable does

| Variable | Where used in code | Effect if missing |
|---|---|---|
| `OPENAI_API_KEY` | `main.py` line 14 | App refuses to start — RuntimeError |
| `PORT` | `main.py` + `Procfile` | App listens on wrong port — Render kills deploy |
| `LLM_MODEL` | `src/generator.py` | Defaults to `gpt-4o-mini` — fine |
| `LANGCHAIN_TRACING_V2` | `main.py` | No tracing — not critical |
| `AUDITOR_API_KEY` | `main.py` guard | API is public — anyone can call it |

---

### 🟠 S14 — How to update an environment variable on Render

1. Go to your service → **Environment** tab
2. Edit the value
3. Click **Save Changes**
4. Render automatically **redeploys** with the new value

---

### 🟠 S15 — How to check if the variable is set correctly

Render masks values after saving (shows `***`). To verify it's working:

```bash
# Check the deploy log — startup prints this if key is missing:
# RuntimeError: OPENAI_API_KEY is not set or is still a placeholder

# Or test the API directly:
curl -X POST https://your-app.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is total revenue?"}'
# If you get a JSON answer — the key is working
```

---

## 🟣 Common Failures & Fixes

> 💡 **Every failure below happened in this project. This section is the hard-earned map of what went wrong and exactly how to fix it.**

---

### 🟣 S16 — "No open ports detected" — Deploy killed instantly

| Symptom | Render kills the deploy within 60 seconds |
|---|---|
| **Cause** | App listening on hardcoded `port=8000`, Render assigned a different port |
| **Fix 1** | Create `Procfile`: `web: uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Fix 2** | In `main.py`: `port=int(os.environ.get("PORT", 8000))` |
| **Verify** | Deploy log should show: `Uvicorn running on http://0.0.0.0:10000` |

---

### 🟣 S17 — "Exited with status 137" — OOM Crash

| Symptom | Deploy starts, then crashes with exit code 137 |
|---|---|
| **Cause** | App used more than 512 MB RAM — Render's free tier limit |
| **Root cause here** | `sentence-transformers` installed (~200 MB) but never used |
| **Fix** | Remove unused heavy libraries from `requirements.txt` |
| **Rule** | Every library in `requirements.txt` must be actively used |
| **Verify** | Deploy log shows `Application startup complete` without crash |

> Exit code 137 = Linux OOM killer terminated the process. It means the OS ran out of memory and forcefully killed your app.

---

### 🟣 S18 — "Search index not found" — API returns 400

| Symptom | App deploys fine but every `/ask` call returns 400 error |
|---|---|
| **Cause** | `data/raw/Tesla.pdf` and `vector_store/` files were in `.gitignore` |
| **Fix** | Remove `data/raw/*` and `vector_store/*` from `.gitignore` |
| **Then** | `git add data/raw/Tesla.pdf vector_store/` and commit |
| **Verify** | `git ls-files vector_store/` shows 5 index files |

---

### 🟣 S19 — Page loads but nothing works — all buttons dead

| Symptom | Page loads, chips and Ask button do nothing when clicked |
|---|---|
| **Cause** | Python `'\n'` inside an HTML string emits a literal newline into JavaScript source. JS syntax error. Browser silently discards the entire `<script>` block. |
| **Fix** | Never use `'\n'` inside Python HTML strings for JS formatting. Use `'<br/>'` directly. |
| **Fix 2** | Use `.replace(/\\n/g, '<br/>')` not `.replace(/\n/g, '\n')` in JS |
| **Verify** | Open browser DevTools → Console tab → no red errors |

---

### 🟣 S20 — Answer box never appears after clicking Ask

| Symptom | Spinner shows briefly, then nothing visible |
|---|---|
| **Cause 1** | `overflow: hidden` on `.demo-card` CSS was clipping the answer box |
| **Fix 1** | Remove `overflow: hidden` from `.demo-card` in CSS |
| **Cause 2** | `classList.add('visible')` unreliable in some browsers |
| **Fix 2** | Use `box.style.display = 'block'` instead |
| **Verify** | Ask a question — answer box should appear and scroll into view |

---

## 🔷 Post-Deployment Verification

> 💡 **Don't just check if the page loads — check if everything actually works end to end.**

---

### 🔷 S21 — Full checklist after every deploy

| Check | How to verify | Expected result |
|---|---|---|
| Page loads | Visit your Render URL | Landing page renders correctly |
| API online badge | Check green dot on page | Shows "API online" |
| Chip auto-submits | Click a sample question chip | Question fills + answer appears |
| Manual question works | Type a question + click Ask | Answer appears with citations |
| Cold start message | First request on free tier | Spinner text mentions "may take 60s" |
| API docs accessible | Visit `/docs` | FastAPI Swagger UI loads |
| No console errors | DevTools → Console | Zero red errors |

---

### 🔷 S22 — How to test the API directly

```bash
# Test the /ask endpoint
curl -X POST https://your-app.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Tesla total revenue?"}'

# Expected response:
{
  "query": "What is Tesla total revenue?",
  "answer": "**Summary:** Tesla reported total revenues of $97.69 billion... [Source: Page 42]"
}

# Test input validation — should return 422
curl -X POST https://your-app.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"query": ""}'
```

---

### 🔷 S23 — How to check Render deploy logs

1. Go to Render dashboard → your service
2. Click **Logs** tab
3. Look for these key lines:

```
# ✅ Good deploy
==> Build successful
==> Deploying...
Application startup complete
Uvicorn running on http://0.0.0.0:10000

# ❌ Bad deploy signals
No open ports detected          → PORT not read from env
Exited with status 137          → OOM — remove heavy libraries
ModuleNotFoundError             → library missing from requirements.txt
RuntimeError: OPENAI_API_KEY    → API key not set in environment
```

---

## 🔴 Monitoring & Cost Management

> 💡 **A deployed app with no monitoring is like a car with no dashboard — you only find out something is wrong when it's too late.**

---

### 🔴 S24 — Monitor with LangSmith (free tier available)

LangSmith traces every GPT call — question, retrieved chunks, answer, latency, token usage.

**Setup:**
1. Sign up at [smith.langchain.com](https://smith.langchain.com)
2. Get your API key
3. Add to Render environment variables:
   ```
   LANGCHAIN_API_KEY=ls-your-key
   LANGCHAIN_TRACING_V2=true
   ```
4. Every `/ask` call now appears in your LangSmith dashboard

**What to watch:**
| Metric | Warning sign |
|---|---|
| Latency | Consistently > 15 seconds → retriever is slow |
| Token usage | Spikes → check for very long queries |
| Error rate | > 5% → check API key, check index |

---

### 🔴 S25 — Manage OpenAI costs

| Action | Saving |
|---|---|
| Use `gpt-4o-mini` not `gpt-4o` | ~20x cheaper per query |
| Set `temperature=0` | Fewer retry calls needed |
| Limit context to top 3 chunks | Shorter prompts = fewer tokens |
| Cache repeated questions | Zero cost for repeated queries |

**Rough cost estimate for this project:**
```
1 question ≈ 1,500 tokens input + 500 tokens output
gpt-4o-mini: $0.15 / 1M input tokens
= ~$0.0002 per question (less than 1 cent)

1,000 questions/month ≈ $0.20/month
```

---

### 🔴 S26 — Interview tips about deployment

> **If asked about costs:**
> *"I'm using Render's free tier for the demo. The app uses gpt-4o-mini at roughly $0.0002 per query — less than one cent. For production at scale, I'd move to a paid Render instance and add Redis caching for repeated queries to drive cost close to zero."*

> **If asked about scaling:**
> *"The current FAISS index is local to the server. For horizontal scaling, I'd move the vector store to Pinecone or Weaviate so multiple server instances can share one index. The FastAPI app itself is stateless and scales horizontally without changes."*

> **If asked why Render and not AWS:**
> *"Render was chosen for speed of deployment and simplicity — no IAM roles, no VPC config, no load balancer setup. For a production enterprise deployment I'd use AWS ECS or GCP Cloud Run, but for a portfolio demo Render gives a live URL in under 5 minutes."*

---

*Last updated: deployment lessons from intelligent-auditor-rag project*
