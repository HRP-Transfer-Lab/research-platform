# Into the Matrix — Alex's Mac setup with Claude Code

**Learner-facing guide — Claude Code + Terminal (no VS Code)**  
**Version:** 0.3 | **Updated:** 13 October 2026  
**Status:** Proposed workshop setup; not yet tested on Alex's Mac  
**First-session goal:** Install the development tools, start Claude Code, and get a **local** Cloudflare Hello World Worker running. No public deployment or model charges without approval.

## The simple idea

Use **Claude Code as the coding assistant** and **Terminal as the workspace**. Alex explains what she wants, Claude Code inspects and edits her local files and can run test commands **subject to her permissions**. She inspects the results, asks questions and approves each meaningful change. She does not need to learn VS Code or write all the code by hand.

**Two different AI roles:** Claude Code is the *development agent* used to construct the workshop application. **Gemma on Cloudflare Workers AI** will be the *model powering the application she builds*. An account for Claude Code does not pay for Cloudflare model inference; these are separate services.

## 0. Prerequisites (about 30 minutes)

- Mac with an internet connection, browser and Terminal (press **Command–Space**, type **Terminal**, Return).
- **macOS 13.5 or later for the complete Cloudflare/Wrangler workshop**. Claude Code's own documented requirement is macOS 13.0+, but use the stricter Cloudflare requirement for this course. Either an Intel or Apple-silicon Mac is suitable.
- **Claude Code access:** an eligible Claude Pro, Max, Team, Enterprise or Anthropic Console account with billing enabled, according to the current Anthropic requirements. A free Claude chat account **does not** include Claude Code.
- **Node.js LTS** to run the Cloudflare tooling, installed from https://nodejs.org/en/download. Node.js is **not required just to install the native Claude Code application**.
- A **separate learning Cloudflare account** from https://dash.cloudflare.com/sign-up for subsequent Gemma/RAG work. Do not use live IQMindware credentials.

**Do not install:** VS Code, GitHub Desktop, Homebrew, Python, Docker, a local LLM or database software for this first workshop. Git is optional.

### Step 1 — check the Mac

In Terminal, run these two commands:

```bash
sw_vers -productVersion
uname -m
```

Record the outputs (`arm64` is Apple silicon; `x86_64` is Intel). If macOS is earlier than **13.5**, ask the instructor before proceeding with Cloudflare setup.

### Step 2 — install Claude Code (official native installer)

Anthropic's current Mac installation command is:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**Review and approve installation of this official third-party tool first.** If you'd rather inspect the installer before running it, discuss that with the instructor. It installs Claude Code on the Mac; it is not a command to deploy the workshop application.

Open a **new Terminal window** and check:

```bash
claude --version
```

If this prints a version number, installation succeeded. If it says `command not found`, see the official [PATH troubleshooting](https://code.claude.com/docs/en/setup) before attempting another installation.

### Step 3 — install Node.js LTS for Cloudflare

Download the official **LTS** macOS installer at https://nodejs.org/en/download. Then reopen Terminal and check:

```bash
node --version
npm --version
```

Both commands should print version numbers. Don't install global Wrangler: the Cloudflare project setup will manage it locally.

### Step 4 — make a safe workshop folder and start Claude Code

```bash
mkdir -p ~/Documents/AgenticAIWorkshop
cd ~/Documents/AgenticAIWorkshop
claude
```

Follow the browser sign-in prompts for the eligible Claude account. Start with the **normal approval/permission prompts**; do not turn on unrestricted command execution or use `--dangerously-skip-permissions`.

The first thing Claude Code sees is only the workshop directory, which keeps this work separated from other personal and business files. It can read and write within its granted permissions; **do not assume every command or file modification is harmless**. Ask it to explain unfamiliar commands before you approve them.

## 1. Give Claude Code the workshop context (about 5 minutes)

The publicly readable resources are:

- [AI Workshops folder](https://github.com/HRP-Transfer-Lab/research-platform/tree/main/workshops/ai)
- [Full curriculum](./INTO_THE_MATRIX_AGENTIC_AI_WORKSHOP.md)
- [Fictional product catalogue](./starter-data/01_demo_catalogue.md)
- [Fictional FAQ](./starter-data/02_demo_faq.md)
- [Fictional evidence rules](./starter-data/03_demo_evidence_rules.md)

Copy and paste this **as a message inside the running Claude Code session**:

> I'm Alex, a beginner on a Mac, working through HRP Transfer Lab's **Into the Matrix** AI workshop. I want to use **Claude Code + Terminal only**, not VS Code. Here are the public workshop materials: https://github.com/HRP-Transfer-Lab/research-platform/tree/main/workshops/ai . Please read the workshop curriculum and Mac setup guide from GitHub; if you cannot access them, explain how you would fetch the public Markdown files safely and ask before doing so. First check my Mac, Node.js and Wrangler readiness. Then take me through the **local Hello World Worker** milestone, one small step at a time. **Explain your intended changes and commands in plain English, seek my approval before installing packages, changing files, accessing accounts or invoking paid APIs, and stop before any public deployment.** Preserve a backup before replacing existing files. Don't request or display secrets, don't touch unrelated folders, and don't enable unrestricted tool permissions. Help me inspect what you did and why, not just produce code.

Claude Code can retrieve the public Markdown files with approved commands (for example `curl` from `raw.githubusercontent.com`). **Do not grant it access to private organisation repositories or other accounts** to make this teaching exercise work.

If Claude cannot read the site, the instructor can supply the workshop files directly. No GitHub login is needed to read these public documents.

## 2. First build — local Cloudflare Hello World (about 20 minutes)

Have Claude Code perform **and explain** the following operations, asking permission at each meaningful step:

1. From `~/Documents/AgenticAIWorkshop`, create a fresh project called **`alex-first-agent`** using Cloudflare's official generator, `npm create cloudflare@latest -- alex-first-agent`. Use a simple **Hello World → Worker only → TypeScript** example, with prompt choices adapted to the current generator. Skip optional Git configuration if Git is absent.
2. **Do not deploy** when the generator asks. No production account should be involved at this stage.
3. Ask Claude to inspect the generated `src/index.ts` and `wrangler.jsonc` (or equivalent filenames), and describe what the entry point and Worker configuration do.
4. Ask it to run `npx wrangler dev` **from the generated project folder**, with approval, and show the address printed by the development server (usually http://localhost:8787).
5. Open the address in a browser to see **Hello World**, then stop the server (Control-C, or have Claude stop it with permission).

Once the new project exists, she can start subsequent sessions in that project directory, so Claude sees the right files:

```bash
cd ~/Documents/AgenticAIWorkshop/alex-first-agent
claude
```

**Pass condition:** A local Worker responds in the browser, and Alex can explain which file controls the response. **This is not yet an AI chatbot or an agent.**

## 3. Optional Cloudflare skills for Claude Code (after the first local success)

Cloudflare documents a [Claude Code integration](https://developers.cloudflare.com/agent-setup/claude-code/) with up-to-date Cloudflare Skills and optional MCP servers. This is **helpful but not necessary for Hello World**. Consider enabling it when beginning Gemma/RAG work.

Inside Claude Code (these are **Claude commands, not shell commands**), after reviewing the plugin's capabilities and agreeing to install:

```text
/plugin marketplace add cloudflare/skills
/plugin install cloudflare@cloudflare
```

The plugin can connect to Cloudflare APIs using OAuth and may offer powerful account operations. **Do not approve production account access or broad write permissions for a learning exercise.** Use a dedicated learning account and read each OAuth permission screen.

## 4. Stage 1 — turn Hello World into a Gemma chatbot (next session)

After the local Worker passes, ask Claude Code to:

- Follow the current [Workers AI + Wrangler tutorial](https://developers.cloudflare.com/workers-ai/get-started/workers-wrangler/).
- Add a Workers AI `AI` binding to the development Worker and use **`@cf/google/gemma-4-26b-a4b-it`** as the *initial model candidate*, after verifying its current availability and syntax.
- Implement a minimal question → model response route; show Alex the actual request and output.
- Run a **single approved test call**, only after checking Cloudflare account eligibility, quotas, data handling and estimated cost.
- Preserve source code and rollback options; do not publicly deploy or include a Cloudflare secret in browser code.

**Cloudflare Workers AI calls run remotely and may incur usage charges even during local development.** The Claude Code subscription is a separate expense. **Pass condition:** one successful inference call, with verified model ID and understandable input/output, but **without RAG or agency yet**.

## 5. Stage 2 — first three knowledge-base uploads

Only once inference works, open the workshop's **separate teaching** Cloudflare account and create an **AI Search** instance using [Cloudflare's getting-started guide](https://developers.cloudflare.com/ai-search/get-started/). Select **built-in document storage** rather than crawling a real company website.

Download or ask Claude Code to download **only** these public teaching files from `workshops/ai/starter-data/`:

1. `01_demo_catalogue.md` — fictional products and availability.
2. `02_demo_faq.md` — fictional support and refund scenario.
3. `03_demo_evidence_rules.md` — evidence boundaries and refusal/uncertainty requirements.

Then upload them via the **AI Search dashboard's document/Items interface**. Follow the current UI labels if Cloudflare changes them. Let Claude Code guide the dashboard steps, but retain human control over the account and uploads.

**Test questions:** “Which resource is free?”, “Can I buy Reasoning Path?”, “Has Focus Foundations been proven to increase IQ?”, and “What are the imaginary refund rules?” Use the retrieved passages to verify each answer. Remember **these are invented teaching facts, not IQMindware prices or policies**.

Do not upload medical information, customer records, unpublished private work, copyrighted third-party papers without permission, .env files, API tokens or credentials.

## 6. Later workshop stages: tools, agency and inspection

Use Claude Code to *build* the same stages specified in the curriculum: (3) read-only structured product lookup → (4) bounded agent selecting from authorised actions → (5) reviewed Cloudflare preview deployment → (6) tests and comparative evaluation.

**The distinctive teaching point:** learners interact with **Claude Code, an existing coding agent**, while constructing a **separate Gemma-based agent**. Inspect Claude's proposed file edits, commands, permission prompts and test results; then compare them with the explicit tool, state, evidence and stop-condition traces of the learner-built agent. Claude's fluent explanations are not by themselves evidence that the learner-built system works.

## 7. What to report after the first session

```text
Mac version (sw_vers -productVersion):
Processor (uname -m):
Claude Code version (claude --version):
Node version (node --version):
npm version (npm --version):
Cloudflare local Worker running? Yes / No
Hello World visible in browser? Yes / No
One thing I learned about what the Worker does:
Non-secret error messages, if any:
```

Never send passwords, session cookies, Anthropic API keys, Cloudflare API tokens, or billing details.

## 8. Troubleshooting

- **`claude: command not found`:** close/reopen Terminal; consult the official [Claude Code install and PATH guide](https://code.claude.com/docs/en/setup).
- **Claude asks for sign-in or payment:** confirm the account has Claude Code access; a free Claude chat account is insufficient.
- **`node: command not found`:** install Node.js LTS and reopen Terminal.
- **Wrangler unsupported macOS error:** confirm version and see [Wrangler's requirements](https://developers.cloudflare.com/workers/wrangler/install-and-update/).
- **The local URL doesn't open:** check whether `npx wrangler dev` is still running; use the exact address printed.
- **Unexpected file changes or installation proposals:** decline, ask Claude to show the diff or planned commands, and approve only after understanding them.
- **AI request denied or usage/billing issue:** stop and check the learning Cloudflare account; do not enter production keys or bypass rate limits.

## Instructor references and safety boundaries

- [Workshop curriculum](./INTO_THE_MATRIX_AGENTIC_AI_WORKSHOP.md)
- [Anthropic: Claude Code native installation and authentication](https://code.claude.com/docs/en/setup)
- [Cloudflare: Claude Code integration](https://developers.cloudflare.com/agent-setup/claude-code/)
- [Cloudflare: Workers AI tutorial](https://developers.cloudflare.com/workers-ai/get-started/workers-wrangler/)
- [Cloudflare: AI Search getting started](https://developers.cloudflare.com/ai-search/get-started/)
- [Cloudflare: AI Search built-in storage](https://developers.cloudflare.com/ai-search/configuration/data-source/built-in-storage/)

**Scope:** These are instructions and fictional starter documents. This update itself does **not** install software on a Mac, create a Cloudflare project, connect accounts, deploy publicly or incur charges.
