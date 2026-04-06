# 🚀 gptnix-toolkit MCP Server

**gptnix-toolkit** is an elite all-in-one Model Context Protocol (MCP) server engineered to quickly supercharge your development workflow. Powered natively by the **Gemini 3.1 Flash** ecosystem, it arms local AI agents with tools to break out of text generation limitations—bridging deep internet research, multimodal image processing, file analysis, and autonomous documentation.

---

## ⚡ Key Features

*   **🧠 Looped Grounding Research:** Autonomously executes dynamic, multi-step web queries behind the scenes before aggregating definitive facts complete with real cited URLs.
*   **🎨 Mutli-Prompt Image Generation:** Transforms text descriptions rapidly into parallel batches of high fidelity images leveraging built-in automated prompt enhancements.
*   **👁️ Multimodal Visual QA:** Feeds screenshots (UI mockups, test crashes, or diagrams) into flash-lite alongside tasks (e.g. "recreate this using Tailwind CSS").
*   **🛠️ Local Image Utilities:** Perform professional, local file-based image processing (`PNG` to `.ICO`, resizing, compression constraints) with zero API costs.
*   **📖 Auto-Documentation:** Drop large arrays of source code directly into Gemini’s 1 Million Token Window and instruct it to extract APIs or fully render structured `.md` docs (like READMEs).

---

## ⚠️ Important Note on API Endpoints and Grounding

This MCP server points to `https://api.gptnix.online/v1/chat/completions` (the GPTNix Endpoint).
**The `gptnix.online` API handles mapping the OpenAI-compatible requests and forcibly enables Google Grounding under the hood for all `google/gemini-*` routed calls.**

If you intend to change `API_URL` to the official Google AI Studio endpoint (`generativelanguage.googleapis.com`) or any other proxy, you **must explicitly ensure** that Google Grounding is supported by that provider via `tools: [{"googleSearch": {}}]`, or the `WebSearch` tool will blindly hallucinate without making live internet queries!

---

## 🏗️ Requirements & Setup

### Prerequisites
*   Python 3.10+
*   The `AKASH_API_KEY` Environment Variable set mapped to the active provider.

### Fast Installation
Create the environment and install dependencies natively:

```bash
# Set up environment
python -m venv venv
source venv/bin/activate
pip install mcp httpx pillow
```

### Adding to Claude Code
Simply add the following to your `~/.claude.json`:
```json
{
  "mcpServers": {
    "gptnix-toolkit": {
      "command": "/path/to/venv/bin/python",
      "args": [
        "/path/to/SearchMCP/server.py"
      ],
      "env": {
        "AKASH_API_KEY": "sk-your-key-here"
      }
    }
  }
}
```

### Adding to VS Code (Roo Code / Cline)
Append to `~/.config/Code/User/mcp.json` (or your respective extension settings):
```json
    "gptnix-toolkit": {
      "command": "/path/to/venv/bin/python",
      "args": [
        "/path/to/SearchMCP/server.py"
      ],
      "env": {
        "AKASH_API_KEY": "sk-your-key-here"
      },
      "type": "stdio"
    }
```

---

## 🛠️ Tool Quick Reference

| Tool Name | Parameters | Capabilities |
| :--- | :--- | :--- |
| `WebSearch` | `query`, `loops` (int: 1-5)| Synthesizes a grounded report after 2 to 5 multi-step Google Searches. |
| `GenerateImage` | `prompts` (list), `output_paths` (list), `input_images` | Parallel asynchronous rendering of multiple custom text-to-image AI payloads. |
| `AnalyzeImage` | `image_path`, `query`| Reads images or screenshots natively to decode structure, read errors, or create UI code. |
| `ProcessImageFormat`| `input_path`, `output_path`, `width`, `height`, `quality` | Converts formats entirely locally using `Pillow`. Supports PNG, JPG, ICO, WEBP. |
| `AutoDocGen` | `file_paths` (list), `instruction` | Evaluates huge source code environments within a 1M context to write Git patches, READMEs, etc. |

For detailed information on parameters and internal logic flow, refer to `DOCS.md`.