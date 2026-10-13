# Into the Matrix — Mac setup and first uploads

**Learner-facing guide (suitable for Alex)**  
**Version:** 0.2 | **Date:** 13 October 2026  
**Status:** Initial setup instructions; not yet confirmed on Alex's particular Mac.  
**Goal for session 0:** Open the course material, create a Cloudflare project and display “Hello World” on the Mac. **Do not deploy or upload sensitive information yet.**

## What you need

A Mac, internet access, a browser, **ChatGPT and Terminal** are the learning interface. Allow about **45–90 minutes** for initial setup. The Cloudflare Wrangler CLI currently requires **macOS 13.5 or newer**. Apple silicon (M-series) and Intel Macs can both be used if their operating system is supported. No graphics card, local model, VS Code, GitHub Desktop, Git, Python, Docker, Homebrew, paid AI subscription or database is required for the first exercise.

**Teaching approach:** ChatGPT explains each step and prepares commands/code; Alex runs commands in Terminal, pastes back non-secret results and asks why things worked (or failed). She should understand and review what commands change. ChatGPT does not automatically operate her Terminal just because she is chatting to it.

### A. Check the Mac first (5 minutes)

Open **Terminal** (press Command–Space, type **Terminal**, press Return). Paste each command separately:

```bash
sw_vers -productVersion
uname -m
```

Record the two outputs. `arm64` means Apple silicon; `x86_64` means Intel. If the macOS version is earlier than **13.5**, stop and ask the workshop instructor about updating macOS or using a browser-hosted development environment.

### B. Install the minimum (15–30 minutes)

| Install / access | Official link | Why |
| --- | --- | --- |
| **ChatGPT** (browser) | https://chatgpt.com/ | Provides beginner-friendly explanations, stepwise commands, code and troubleshooting. |
| **Terminal** (already on the Mac) | Applications → Utilities → Terminal | Runs the instructions and checks the application. |
| **Node.js — current LTS release** | https://nodejs.org/en/download | Installs `node` and `npm` to run Cloudflare tools. Choose the official macOS installer. |
| **Cloudflare account** (for the AI stage) | https://dash.cloudflare.com/sign-up | Needed for remote Gemma inference, AI Search and public deployment. Use a workshop account, never the live IQMindware account. |

**Entirely optional:** [GitHub Desktop](https://desktop.github.com/download/), [VS Code](https://code.visualstudio.com/download), a GitHub account, and Git. The course documents are publicly readable on GitHub and can be downloaded with `curl` in Terminal. A text editor is optional; ChatGPT can supply commands to display and update project files. Python, Docker, Postgres, R2 and a locally installed model are not needed at this stage.

After installing Node.js, **close and reopen Terminal**, then run:

```bash
node --version
npm --version
```

Both should return version numbers. If Node is missing, reopen Terminal or revisit the installer. Never paste passwords, API tokens, account cookies or credential screenshots into ChatGPT or a public support thread.

## 1. Get the workshop files — no Git installation (5–10 minutes)

All course documents are public:  
https://github.com/HRP-Transfer-Lab/research-platform/tree/main/workshops/ai

**Simplest route:** open the links in the browser and read the [curriculum](./INTO_THE_MATRIX_AGENTIC_AI_WORKSHOP.md) and this guide. The instructor can provide the three small sample Markdown files separately when it is time to upload them.

**To put the files on the Mac using Terminal**, paste this complete block (it downloads only public documents from the workshop folder; it does not run them):

```bash
mkdir -p ~/Documents/AgenticAIWorkshop/workshop-files/starter-data
cd ~/Documents/AgenticAIWorkshop/workshop-files
BASE='https://raw.githubusercontent.com/HRP-Transfer-Lab/research-platform/main/workshops/ai'
curl -fL "$BASE/README.md" -o README.md
curl -fL "$BASE/INTO_THE_MATRIX_AGENTIC_AI_WORKSHOP.md" -o INTO_THE_MATRIX_AGENTIC_AI_WORKSHOP.md
curl -fL "$BASE/ALEX_MAC_GETTING_STARTED.md" -o ALEX_MAC_GETTING_STARTED.md
curl -fL "$BASE/starter-data/01_demo_catalogue.md" -o starter-data/01_demo_catalogue.md
curl -fL "$BASE/starter-data/02_demo_faq.md" -o starter-data/02_demo_faq.md
curl -fL "$BASE/starter-data/03_demo_evidence_rules.md" -o starter-data/03_demo_evidence_rules.md
ls -l starter-data
```

To read a file in Terminal:

```bash
less INTO_THE_MATRIX_AGENTIC_AI_WORKSHOP.md
```

Press **q** to exit the viewer. You can also open Markdown files with any text editor already on the Mac. GitHub Desktop, Git and VS Code are optional if Alex later wants source control or a visual editor.

### The first six files

```text
AgenticAIWorkshop/
  workshop-files/
    README.md                               ← workshop catalogue
    INTO_THE_MATRIX_AGENTIC_AI_WORKSHOP.md  ← full curriculum
    ALEX_MAC_GETTING_STARTED.md             ← this guide
    starter-data/
      01_demo_catalogue.md                  ← fictitious product information
      02_demo_faq.md                        ← fictitious support facts
      03_demo_evidence_rules.md             ← evidence/claim boundaries
```

These **starter-data files are fictional teaching fixtures**, not current IQMindware facts or validated efficacy evidence. They can later be uploaded to a separate learning-only AI Search instance. Public files may be read without logging in to GitHub.

## 2. Create the first app on your Mac (10–20 minutes)

**Important:** Put the app **beside** `workshop-files`, not inside it, to separate learning materials from code that can change.

In Terminal:

```bash
cd ~/Documents/AgenticAIWorkshop
npm create cloudflare@latest -- alex-first-agent
```

If asked whether to install the setup package, accept. For the prompts, choose:

- **Hello World example**
- **Worker only**
- **TypeScript**
- **Use Git for version control:** No (for the first lesson, unless Git is already installed and desired)
- **Add AGENTS.md:** Yes, if offered
- **Deploy now:** **No**

The names of prompts may vary as Cloudflare updates its setup wizard. It should generate `alex-first-agent/src/index.ts` and `alex-first-agent/wrangler.jsonc` (or the current equivalent), with Wrangler installed as a **project dependency**. Do not install Wrangler globally.

Now run:

```bash
cd ~/Documents/AgenticAIWorkshop/alex-first-agent
npx wrangler --version
npx wrangler dev
```

Open the URL printed by Wrangler, usually **http://localhost:8787**. You should see a Hello World response. If not, copy the **non-secret error text** for the instructor. Leave the Terminal window running while testing; press **Control-C** to stop it.

**Success criterion for session 0:** You can open a locally running Worker in the browser and inspect the project files **in Terminal**, for example:

```bash
ls
sed -n '1,100p' src/index.ts
```

If `src/index.ts` has a different name in the wizard's template, ask ChatGPT to help locate the actual file. Nothing has been publicly deployed and no AI inference has been required.

## 3. First model call — instructor-led next step

After the local Worker succeeds, follow the current [Cloudflare Workers AI tutorial](https://developers.cloudflare.com/workers-ai/get-started/workers-wrangler/) to add the `AI` binding to `wrangler.jsonc`, update `src/index.ts`, and call the model `@cf/google/gemma-4-26b-a4b-it`.

The model is **cloud-hosted**, so it does not run on the Mac. **Cloudflare warns that Workers AI calls are remote and may incur usage charges even while using local development**. Before the first call, check plan eligibility, quotas and spending controls with the instructor. Use a teaching account, not IQMindware production.

The instructor should provide a known-good Worker starter and a limited test budget for this stage. **No graphical editor is required:** Alex can paste the current `src/index.ts` and `wrangler.jsonc` contents (with all secrets removed) into ChatGPT, ask it to explain the edit, then use a reviewed Terminal command to save the change. Before replacing a file, keep a backup, e.g. `cp src/index.ts src/index.ts.bak`. Do **not** run `npx wrangler deploy` until public deployment is explicitly approved. A successful model response is **stage 1**, not yet a RAG chatbot or agent.

## 4. First *uploads* — three knowledge-base documents (stage 2, not day 0)

Once stage 1 works, create a **separate learning instance** of Cloudflare AI Search in Alex's account (or an instructor-controlled sandbox) using the [AI Search dashboard guide](https://developers.cloudflare.com/ai-search/get-started/). For a simple teaching example, choose **built-in storage**, rather than crawling a website.

In Cloudflare's dashboard, open **AI → AI Search → [your learning instance] → Items**, and upload just:

1. `starter-data/01_demo_catalogue.md`
2. `starter-data/02_demo_faq.md`
3. `starter-data/03_demo_evidence_rules.md`

These files are already in the workshop repository. AI Search's built-in storage supports direct document uploads and indexing. The instructor can demonstrate searches and show which passage supports a response.

**Try these questions:**

- “Which Demo Cognitive Lab resource is free?”
- “Is the Reasoning Path available now?”
- “What should the assistant say about proven IQ gains?”
- “What is the refund policy for the fictional product?”
- “What if somebody asks it for a medical diagnosis?”

**Do not upload:** actual customer correspondence; private GitHub documents; third-party copyrighted papers without rights; Stripe data; API keys; .env files; medical details; real participant information or company secrets.

No need to connect Alex's Cloudflare account to **iqmindware.com**: a website crawl requires control/authorisation of the relevant domain on that Cloudflare account and is unnecessary for this workshop.

## 5. What to send the instructor after session 0

Share **only**:

```text
Mac version (sw_vers -productVersion):
Mac processor (uname -m):
Node version (node --version):
npm version (npm --version):
Cloudflare Wrangler version (npx wrangler --version):
Local Hello World visible in browser? Yes / No
Any non-secret error message:
```

**Never send:** Cloudflare API tokens, GitHub personal access tokens, passwords, session cookies, SSH private keys or billing details.

## 6. Common Mac problems

- **“command not found: node”** — make sure the macOS Node.js LTS installer finished, then reopen Terminal.
- **Wrangler says unsupported macOS** — check the OS version and the [current Wrangler requirements](https://developers.cloudflare.com/workers/wrangler/install-and-update/).
- **Cannot open the local URL** — check that `npx wrangler dev` is still running and use the *exact* address it prints.
- **Cloudflare asks you to authenticate during AI use** — use your own learning account and the normal browser login; do not share credentials.
- **Mac permissions or package errors** — do not use `sudo npm install -g`; ask the instructor to review the error and Node installation.

## One-time ChatGPT coaching prompt

Paste this into a new ChatGPT conversation when starting the workshop:

> I am following HRP Transfer Lab's *Into the Matrix* beginner workshop on a Mac. I am using **ChatGPT + Terminal only**, without VS Code, GitHub Desktop or previous coding experience. Give me one safe Terminal command or short command block at a time, explain what it does and what output to expect, then wait for my result. Do not assume you can control my computer or read files I have not provided. Keep all AI keys server-side, never ask me to paste secrets, back up files before replacing them, and do not deploy publicly or incur AI usage charges without explaining the step first. Help me understand the model, retrieval, tools and agent-loop components, not merely copy commands.

## Instructor notes and original documentation

- [Full workshop curriculum](./INTO_THE_MATRIX_AGENTIC_AI_WORKSHOP.md).
- [Cloudflare Workers AI with Wrangler](https://developers.cloudflare.com/workers-ai/get-started/workers-wrangler/).
- [Wrangler install and system requirements](https://developers.cloudflare.com/workers/wrangler/install-and-update/).
- [Cloudflare AI Search built-in document upload](https://developers.cloudflare.com/ai-search/configuration/data-source/built-in-storage/).

**Scope:** This guide supplies setup instructions and public, synthetic documents. It does not deploy anything to Cloudflare, install software on Alex's computer, create an account, grant access or incur charges.
