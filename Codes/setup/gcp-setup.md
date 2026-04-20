# Google Cloud + Vertex AI Setup Guide

## What You Need

- A GCP project with billing enabled
- Vertex AI API enabled
- Application Default Credentials (ADC) configured locally

---

## Step 1 — Install the Google Cloud CLI

```bash
# macOS (Homebrew)
brew install --cask google-cloud-sdk

# Verify
gcloud version
```

---

## Step 2 — Authenticate

```bash
# Login to your Google account
gcloud auth login

# Set up Application Default Credentials (used by ADK + Vertex AI SDK)
gcloud auth application-default login
```

---

## Step 3 — Configure Your Project

```bash
# Replace YOUR_PROJECT_ID with your GCP project ID
gcloud config set project YOUR_PROJECT_ID

# Verify
gcloud config list
```

---

## Step 4 — Enable Required APIs

```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable generativelanguage.googleapis.com
```

---

## Step 5 — Set Environment Variables

Add to your `.env` file (copy from `.env.example`):

```
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1
```

---

## Step 6 — Verify Vertex AI Access

```python
import vertexai
from vertexai.generative_models import GenerativeModel

vertexai.init(project="YOUR_PROJECT_ID", location="us-central1")
model = GenerativeModel("gemini-2.0-flash")
response = model.generate_content("Say hello")
print(response.text)
```

---

## ADK-Specific: Using Vertex AI as the Backend

In ADK, swap the model backend from Gemini API to Vertex AI by setting:

```python
import os
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
os.environ["GOOGLE_CLOUD_PROJECT"] = "your_project_id"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
```

Or in `.env`:
```
GOOGLE_GENAI_USE_VERTEXAI=True
```

All ADK examples in `vertex-ai-real-world/` use this flag.

---

## Available Models on Vertex AI

| Model | Use Case |
|---|---|
| `gemini-2.0-flash` | Fast, cost-efficient — default for most examples |
| `gemini-2.0-pro` | Higher reasoning quality |
| `gemini-1.5-pro` | Long context (1M tokens) |
| `gemini-1.5-flash` | Balanced speed + quality |

---

## Troubleshooting

**Error: `google.auth.exceptions.DefaultCredentialsError`**
→ Run `gcloud auth application-default login` again.

**Error: `403 PERMISSION_DENIED`**
→ Check that Vertex AI API is enabled: `gcloud services list --enabled | grep aiplatform`

**Error: `404 models/gemini not found`**
→ Ensure `GOOGLE_CLOUD_LOCATION` is set to a region that supports the model (e.g., `us-central1`).
