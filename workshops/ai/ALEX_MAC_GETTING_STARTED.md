# Into the Matrix — Mac setup and first uploads

**Learner-facing guide (suitable for Alex)**  
**Version:** 0.1 | **Date:** 13 October 2026  
**Status:** Initial setup instructions; not yet confirmed on Alex's particular Mac.  
**Goal for session 0:** Open the course material, create a Cloudflare project and display “Hello World” on the Mac. **Do not deploy or upload sensitive information yet.**

## What you need

A Mac, internet access, a web browser, and about **45–90 minutes** for the initial setup. The Cloudflare Wrangler CLI currently requires **macOS 13.5 or newer**. Apple silicon (M-series) and Intel Macs are both suitable provided the operating system is supported. No dedicated graphics card, local model, Python, Docker, Homebrew, paid AI subscription or database is needed initially.

### A. Check the Mac first (5 minutes)

Open **Terminal** (press Command–Space, type **Terminal**, press Return). Paste each command separately:

```bash
sw_vers -productVersion
uname -m
```

Record the two outputs. `arm64` means Apple silicon; `x86_64` means Intel. If the macOS version is earlier than **13.5**, stop and ask the workshop instructor about updating macOS or using a browser-hosted development environment.

### B. Install only these essentials (15–30 minutes)

| Install / access | Official link | What it is for |
| --- | --- | --- |
| **Visual Studio Code (VS Code)** | https://code.visualstudio.com/download | Editing and reading workshop code and Markdown. Choose the Mac build compatible with your processor, if offered. |
| **Node.js — current LTS release** | https://nodejs.org/en/download | Lets your Mac run the Cloudflare setup tools. Choose the official macOS installer; it includes npm. |
| **GitHub Desktop** (recommended for beginners) | https://desktop.github.com/download/ | Open and update GitHub repositories using a graphical interface. Terminal Git is an alternative. |
| **GitHub account** | https://github.com/signup | Optional for reading public workshop files; useful for saving your own project or collaborating. |
| **Cloudflare account** | https://dash.cloudflare.com/sign-up | Needed when connecting the model or eventually deploying a Worker. Use your own learning account, not the live IQMindware account. |

**Optional:** Use the Mac's built-in **TextEdit** or VS Code to read the provided Markdown. You do not need to install Python, Docker, Postgres, Cloudflare R2, vector database software or an AI model.

After installing Node.js, **close and reopen Terminal**, then run:

```bash
node --version
npm --version
git --version
```

The first two should display version numbers. If Git is missing, macOS may offer to install Apple Command Line Tools; alternatively install GitHub Desktop. If a new installation is not found, quit/reopen Terminal before troubleshooting. **Do not post account tokens, passwords or credential screenshots.**

## 1. Download the course files (5–10 minutes)

Repository (public workshop materials):  
https://github.com/HRP-Transfer-Lab/research-platform/tree/main/workshops/ai

**Recommended no-code method:**
1. Open [GitHub Desktop](https://desktop.github.com/download/).
2. Choose **File → Clone Repository → URL**.
3. Enter `https://github.com/HRP-Transfer-Lab/research-platform.git`.
4. Save it in `Documents/AgenticAIWorkshop/research-platform`.
5. In GitHub Desktop choose **Repository → Open in Visual Studio Code** (or open the folder manually in VS Code).
6. Read `workshops/ai/INTO_THE_MATRIX_AGENTIC_AI_WORKSHOP.md`.

**Terminal alternative:**

```bash
mkdir -p ~/Documents/AgenticAIWorkshop
cd ~/Documents/AgenticAIWorkshop
git clone https://github.com/HRP-Transfer-Lab/research-platform.git
```

Reading/cloning this public repository does not give you write permissions to the organisation. Do not commit changes to the shared repository without explicit permission.

### First files to locate

```text
research-platform/
  workshops/
    ai/
      README.md                               ← workshop catalogue
      INTO_THE_MATRIX_AGENTIC_AI_WORKSHOP.md  ← full curriculum
      ALEX_MAC_GETTING_STARTED.md             ← this guide
      starter-data/
        01_demo_catalogue.md                  ← fictitious product information
        02_demo_faq.md                        ← fictitious support facts
        03_demo_evidence_rules.md             ← scientific claim boundaries
```

These **starter-data files are deliberately fictional teaching fixtures**, not live IQMindware data or validated scientific evidence. They are safe to read locally and later upload to a *separate learning-only AI Search instance*.

## 2. Create the first app on your Mac (10–20 minutes)

**Important:** Put the new app **beside** `research-platform`, not inside it. This keeps your experiments separate from the organisation's repository.

In Terminal:

```bash
cd ~/Documents/AgenticAIWorkshop
npm create cloudflare@latest -- alex-first-agent
```

If asked whether to install the setup package, accept. For the prompts, choose:

- **Hello World example**
- **Worker only**
- **TypeScript**
- **Use Git for version control:** Yes
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

**Success criterion for session 0:** You can open `alex-first-agent` in VS Code, see the source files and load a locally running Worker in the browser. Nothing has been publicly deployed and no AI inference has been required.

## 3. First model call — instructor-led next step

After the local Worker succeeds, follow the current [Cloudflare Workers AI tutorial](https://developers.cloudflare.com/workers-ai/get-started/workers-wrangler/) to add the `AI` binding to `wrangler.jsonc`, update `src/index.ts`, and call the model `@cf/google/gemma-4-26b-a4b-it`.

The model is **cloud-hosted**, so it does not run on the Mac. **Cloudflare warns that Workers AI calls are remote and may incur usage charges even while using local development**. Before the first call, check plan eligibility, quotas and spending controls with the instructor. Use a teaching account, not IQMindware production.

The instructor should provide a known-good Worker starter and a limited test budget for this stage. Do **not** run `npx wrangler deploy` until a public deployment has been explicitly approved. A successful model response is **stage 1**, not yet a RAG chatbot or agent.

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
Git version (git --version):
Cloudflare Wrangler version (npx wrangler --version):
Local Hello World visible in browser? Yes / No
Any non-secret error message:
```

**Never send:** Cloudflare API tokens, GitHub personal access tokens, passwords, session cookies, SSH private keys or billing details.

## 6. Common Mac problems

- **“command not found: node”** — make sure the macOS Node.js LTS installer finished, then reopen Terminal.
- **“command not found: git”** — follow Apple's Command Line Tools prompt or use GitHub Desktop.
- **Wrangler says unsupported macOS** — check the OS version and the [current Wrangler requirements](https://developers.cloudflare.com/workers/wrangler/install-and-update/).
- **Cannot open the local URL** — check that `npx wrangler dev` is still running and use the *exact* address it prints.
- **Cloudflare asks you to authenticate during AI use** — use your own learning account and the normal browser login; do not share credentials.
- **Mac permissions or package errors** — do not use `sudo npm install -g`; ask the instructor to review the error and Node installation.

## Instructor notes and original documentation

- [Full workshop curriculum](./INTO_THE_MATRIX_AGENTIC_AI_WORKSHOP.md).
- [Cloudflare Workers AI with Wrangler](https://developers.cloudflare.com/workers-ai/get-started/workers-wrangler/).
- [Wrangler install and system requirements](https://developers.cloudflare.com/workers/wrangler/install-and-update/).
- [Cloudflare AI Search built-in document upload](https://developers.cloudflare.com/ai-search/configuration/data-source/built-in-storage/).

**Scope:** This guide supplies setup instructions and public, synthetic documents. It does not deploy anything to Cloudflare, install software on Alex's computer, create an account, grant access or incur charges.
