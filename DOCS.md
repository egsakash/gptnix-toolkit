# gptnix-toolkit MCP Documentation

## Overview
`gptnix-toolkit` is an all-in-one Model Context Protocol (MCP) server providing an elite creative and research suite. It brings powerful tools to any connected AI agent: deep web research, image generation, vision/file analysis, and local image format processing.

---

## File Structure & Execution
Codebase path: `/home/akash/Desktop/NewProjects/SearchMCP/`

*   **`server.py`**: The MCP server logic exposing the functionality.
*   **Virtual Environment**: Runs via `/home/akash/venv/bin/python` containing dependencies (`mcp`, `httpx`, `Pillow`).
*   **API Key**: `AKASH_API_KEY` must be exposed in the server configuration environments via `mcp.json` / `.claude.json`.

---

## Enabled Tools

### 1. `WebSearch`
Comprehensive internet search capability powered by `google/gemini-3.1-flash-lite-preview`.
Uses a **"Looped Grounding"** strategy, streaming internally, to autonomously iteratively search the internet up to 5 times to synthesize a final, heavily fact-checked response with cited sources.

*   **Arguments:**
    *   `query` *(string)*: The research topic. Provide **targeted, well-instructed queries** (e.g., "Find the specific API changes in React 19 beta"). Do not use generic phrases like "search the whole internet".
    *   `loops` *(int, Optional)*: Number of background search iterations (1 to 5). Defaults to `2`.

### 2. `GenerateImage`
Text-to-Image generation model powered by `google/gemini-3.1-flash-image-preview`. 
It accepts a list of text prompts and concurrently requests them to generate multiple distinct images in a single FastMCP tool call. It can process up to 10 distinct generative requests concurrently per call.

*   **Arguments:**
    *   `prompts` *(list[string])*: A list of text descriptions. Each prompt in the list will generate one independent image.
    *   `output_paths` *(list[string], Optional)*: Array of FULL ABSOLUTE file paths defining where to save each corresponding generated image. Must match the length of `prompts`.
    *   `input_images` *(list[string], Optional)*: Array of local file paths (ABSOLUTE) representing reference image context. These images are applied contextually to ALL prompts in the current batch.

### 3. `AnalyzeImage`
Vision capabilities powered by `google/gemini-3.1-flash-lite-preview`. Extracts information or code from local images.

*   **Arguments:**
    *   `image_path` *(string)*: FULL ABSOLUTE path to the image file (mockups, diagrams, screenshots).
    *   `query` *(string)*: Instructions for the AI (e.g. "Write React code to recreate this UI").

### 4. `ProcessImageFormat`
Local image utility powered by `Pillow` to convert formats (PNG, WEBP, ICO, JPG, etc.), resize, or change quality locally.

*   **Arguments:**
    *   `input_path` *(string)*: FULL ABSOLUTE path to source image.
    *   `output_path` *(string)*: FULL ABSOLUTE path to destination image. Extension determines format.
    *   `width` *(int, Optional)*: New width.
    *   `height` *(int, Optional)*: New height.
    *   `quality` *(int, Optional)*: Quality for JPEG/WEBP (1-100, default 90).

### 5. `AutoDocGen`
Massive codebase documentation tool leveraging Gemini 3.1 Flash Lite's 1M context window. Pass huge project files and let the AI instantly generate beautiful READMEs, inline docs, or architecture analyses.

*   **Arguments:**
    *   `file_paths` *(list[string])*: Array of FULL ABSOLUTE paths to raw source code files. (Max 50 files/1MB per file cap).
    *   `instruction` *(string, Optional)*: Specialized documentation instructions (e.g., "Generate a beautiful README" or "Write inline API spec"). Default is README format.
This toolkit is globally linked to:
1. **Claude Code CLI**: `~/.claude.json`
2. **VS Code Global**: `~/.config/Code/User/mcp.json`
3. **Cline Extension**: `~/.config/Code/User/globalStorage/kilocode.kilo-code/settings/mcp_settings.json`
