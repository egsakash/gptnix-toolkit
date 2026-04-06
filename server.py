import os
import httpx
import base64
import mimetypes
from datetime import datetime
from PIL import Image
from mcp.server.fastmcp import FastMCP
from prompts import SEARCH_PROMPT, IMAGE_ENHANCE_PROMPT, DOC_GEN_PROMPT

mcp = FastMCP(
    "gptnix-toolkit",
    instructions="Elite toolkit powered by Gemini Flash 3.1. Provides deep web research via looped grounding, file analysis, and image generation."
)

API_URL = "https://api.gptnix.online/v1/chat/completions"
SEARCH_MODEL = "google/gemini-3.1-flash-lite-preview"
IMAGE_MODEL = "google/gemini-3.1-flash-image-preview"

def get_headers():
    key = os.getenv("AKASH_API_KEY")
    if not key:
        raise ValueError("AKASH_API_KEY not set")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

async def call_api_loop(query: str, loops: int = 2, temperature: float = 0.2) -> str:
    messages = [
        {"role": "system", "content": SEARCH_PROMPT},
        {"role": "user", "content": f"Initial query: {query}. Begin step 1 research."}
    ]

    async with httpx.AsyncClient(timeout=120.0) as client:
        payload = {"model": SEARCH_MODEL, "temperature": temperature, "messages": messages, "stream": True}

        # Step 1: Initial Query
        async with client.stream("POST", API_URL, headers=get_headers(), json=payload) as r:
            r.raise_for_status()
            current_response = ""
            async for chunk in r.aiter_text():
                if chunk.startswith("data: ") and chunk != "data: [DONE]\n\n":
                    import json
                    try:
                        data = json.loads(chunk[6:])
                        if content := data.get("choices", [{}])[0].get("delta", {}).get("content"):
                            current_response += content
                            # yield current_response if we were implementing true MCP stream wrapper
                    except json.JSONDecodeError:
                        pass
            messages.append({"role": "model", "content": current_response})

        # Loop steps 2 to loops
        for step in range(2, loops + 1):
            messages.append({"role": "user", "content": f"Continue. This is step {step}. Find different/deeper aspects."})
            payload["messages"] = messages
            async with client.stream("POST", API_URL, headers=get_headers(), json=payload) as r:
                r.raise_for_status()
                current_response = ""
                async for chunk in r.aiter_text():
                    if chunk.startswith("data: ") and chunk != "data: [DONE]\n\n":
                        import json
                        try:
                            data = json.loads(chunk[6:])
                            if content := data.get("choices", [{}])[0].get("delta", {}).get("content"):
                                current_response += content
                        except json.JSONDecodeError:
                            pass
                messages.append({"role": "model", "content": current_response})

        # Final Step: Compile
        messages.append({"role": "user", "content": "Final Answer. Compile everything into the required final format."})
        payload["messages"] = messages

        final_answer = ""
        async with client.stream("POST", API_URL, headers=get_headers(), json=payload) as r:
            r.raise_for_status()
            async for chunk in r.aiter_text():
                if chunk.startswith("data: ") and chunk != "data: [DONE]\n\n":
                    import json
                    try:
                        data = json.loads(chunk[6:])
                        if content := data.get("choices", [{}])[0].get("delta", {}).get("content"):
                            final_answer += content
                    except json.JSONDecodeError:
                        pass
        return final_answer

@mcp.tool()
async def WebSearch(query: str, loops: int = 2) -> str:
    """
    Comprehensive, deep internet search using Looped Grounding.
    Args:
        query: The search query. Provide targeted, well-instructed queries. Do not use generic phrases like "search the whole internet".
        loops: Number of search loops to perform (1 to 5). Defaults to 2.
    """
    loops = max(1, min(5, loops))
    return await call_api_loop(query, loops=loops)

@mcp.tool()
async def GenerateImage(prompts: list[str], output_paths: list[str] = None, input_images: list[str] = None) -> str:
    """
    Generate one or multiple images using the Gemini Flash Image model.
    To ensure high quality, provide EXTREMELY detailed, exact, and structurally perfect prompts. Do not use short or ambiguous terms.
    Args:
        prompts: A list of text descriptions. Each prompt in the list will generate one image. Max 5 allowed to prevent rate limiting.
        output_paths: Optional list of FULL ABSOLUTE file paths to save the images. Must match the length of prompts if provided. ALWAYS use ABSOLUTE paths.
        input_images: Optional list of FULL ABSOLUTE image file paths to use as reference/input. Applied to all generated images in this batch.
    """
    input_images = input_images or []

    if isinstance(prompts, str):
        prompts = [prompts]

    if output_paths and isinstance(output_paths, str):
        output_paths = [output_paths]

    if output_paths and len(output_paths) != len(prompts):
        return f"Error: Number of output_paths ({len(output_paths)}) does not match number of prompts ({len(prompts)})."

    # Cap to max 5 concurrent requests
    prompts = prompts[:5]

    # Base payload construction for shared inputs
    base_content = []

    for img_path in input_images:
        if not os.path.exists(img_path):
            return f"Error: Input image file not found: {img_path}"

        mime_type, _ = mimetypes.guess_type(img_path)
        if not mime_type or not mime_type.startswith("image/"):
            mime_type = "image/jpeg"

        with open(img_path, "rb") as f:
            b64_img = base64.b64encode(f.read()).decode("utf-8")

        data_url = f"data:{mime_type};base64,{b64_img}"
        base_content.append({
            "type": "image_url",
            "image_url": {"url": data_url}
        })

    saved_files = []
    errors = []

    import asyncio

    async def enhance_prompt(client: httpx.AsyncClient, prompt_text: str) -> str:
        payload = {
            "model": SEARCH_MODEL,
            "messages": [
                {"role": "system", "content": IMAGE_ENHANCE_PROMPT},
                {"role": "user", "content": f"Enhance this prompt:\n{prompt_text}"}
            ]
        }
        try:
            r = await client.post(API_URL, headers=get_headers(), json=payload)
            if r.status_code == 200:
                enhanced = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                if enhanced:
                    return enhanced.strip()
        except:
            pass
        # Fallback to original prompt if enhancement fails
        return prompt_text

    async def request_image(idx, prompt_text):
        async with httpx.AsyncClient(timeout=120.0) as client:
            # First, enhance the prompt
            enhanced_prompt_text = await enhance_prompt(client, prompt_text)

            content = [{"type": "text", "text": enhanced_prompt_text}] + base_content
            payload = {
                "model": IMAGE_MODEL,
                "messages": [
                    {"role": "user", "content": content}
                ],
                "modalities": ["image", "text"]
            }

            try:
                r = await client.post(API_URL, headers=get_headers(), json=payload)
                if r.status_code != 200:
                    return None, f"Prompt [{idx+1}] Failed API Error ({r.status_code}): {r.text} | Attempted Prompt: '{enhanced_prompt_text[:50]}...'"

                data = r.json()
                choices = data.get("choices", [])
                if not choices:
                    return None, f"Prompt [{idx+1}] Error: No choices returned from the model."

                message = choices[0].get("message", {})
                images = message.get("images", [])

                if not images:
                    return None, f"Prompt [{idx+1}] Error: No image found for prompt '{enhanced_prompt_text[:50]}...'"

                b64_data_url = images[0].get("image_url", {}).get("url", "")
                if not b64_data_url:
                    return None, f"Prompt [{idx+1}] Error: Image URL empty for prompt '{enhanced_prompt_text[:50]}...'"

                b64_string = b64_data_url.split(",")[1] if "," in b64_data_url else b64_data_url

                # Path resolution
                if output_paths and len(output_paths) > idx:
                    target_path = os.path.abspath(output_paths[idx])
                    os.makedirs(os.path.dirname(target_path) or ".", exist_ok=True)
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    target_path = os.path.abspath(f"image_{idx+1}_{timestamp}.png")

                with open(target_path, "wb") as f:
                    f.write(base64.b64decode(b64_string))

                return target_path, None
            except Exception as exc:
                return None, f"Prompt [{idx+1}] Exception: {str(exc)}"

    # Run requests concurrently
    tasks = [request_image(idx, pt) for idx, pt in enumerate(prompts)]
    results = await asyncio.gather(*tasks)

    for path, err in results:
        if path:
            saved_files.append(path)
        if err:
            errors.append(err)

    result_str = ""
    if saved_files:
        result_str += "Success! Images saved to:\n" + "\n".join(f"- {f}" for f in saved_files)

    if errors:
        result_str += "\n\nErrors encountered:\n" + "\n".join(f"- {e}" for e in errors)
        if not saved_files:
            return result_str

    return result_str

@mcp.tool()
async def AnalyzeImage(image_path: str, query: str) -> str:
    """
    Analyze local images (screenshots, UI mockups, diagrams) and answer questions or write code based on them.
    Args:
        image_path: FULL ABSOLUTE path to the image file to analyze.
        query: What to do with the image (e.g., "Write React code to recreate this UI" or "What does this diagram show?").
    """
    if not os.path.exists(image_path):
        return f"Error: Image file not found: {image_path}"

    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type or not mime_type.startswith("image/"):
        # Attempt fallback
        mime_type = "image/jpeg"

    try:
        with open(image_path, "rb") as f:
            b64_img = base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        return f"Error reading image: {e}"

    data_url = f"data:{mime_type};base64,{b64_img}"

    payload = {
        "model": SEARCH_MODEL, # Flash Lite is fast and capable for multimodal tasks
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": query},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]
            }
        ]
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(API_URL, headers=get_headers(), json=payload)
        if r.status_code != 200:
            return f"API Error ({r.status_code}): {r.text}"

        data = r.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "Error: No content returned")

@mcp.tool()
async def ProcessImageFormat(input_path: str, output_path: str, width: int = None, height: int = None, quality: int = 90) -> str:
    """
    Convert image formats, resize, or compress local images. Supported formats: PNG, JPEG, WEBP, ICO, GIF, BMP.
    Args:
        input_path: FULL ABSOLUTE path to the source image.
        output_path: FULL ABSOLUTE path for the destination image. The format is determined by the file extension (e.g. .ico, .webp, .jpg).
        width: Optional new width in pixels.
        height: Optional new height in pixels.
        quality: Optional quality for JPEG/WEBP (1-100, default 90).
    """
    if not os.path.exists(input_path):
        return f"Error: Input image not found: {input_path}"

    try:
        with Image.open(input_path) as img:
            # Resize if requested
            if width or height:
                w = width or img.width
                h = height or img.height
                img = img.resize((w, h), Image.Resampling.LANCZOS)

            # Convert mode if necessary for certain formats (e.g. JPEG doesn't support RGBA)
            ext = os.path.splitext(output_path)[1].lower()
            if ext in ['.jpg', '.jpeg'] and img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            elif ext == '.ico':
                # ICOs require specific sizing, optionally handle it here
                pass

            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

            # Save format specific options
            save_kwargs = {}
            if ext in ['.jpg', '.jpeg', '.webp']:
                save_kwargs['quality'] = quality

            img.save(output_path, **save_kwargs)
            return f"Successfully processed and saved image to {os.path.abspath(output_path)} (Size: {img.width}x{img.height})"

    except Exception as e:
        return f"Error processing image: {e}"

@mcp.tool()
async def AutoDocGen(file_paths: list[str], instruction: str = "Generate comprehensive documentation (README format) for these files.") -> str:
    """
    Generate professional Markdown documentation from massive source code contexts.
    Uses Gemini 3.1 Flash Lite's 1 Million token window to analyze entire project structures at once.
    Args:
        file_paths: A list of FULL ABSOLUTE file paths to the source code files you want to document.
        instruction: Specific instructions (e.g., 'Generate a README', 'Write inline docs for all auth functions'). Default is a general README format.
    """
    if isinstance(file_paths, str):
        file_paths = [file_paths]

    MAX_FILES = 50 # Cap to prevent memory/payload explosion locally
    if len(file_paths) > MAX_FILES:
        file_paths = file_paths[:MAX_FILES]

    documents = []

    # Read all files locally
    for path in file_paths:
        if not os.path.exists(path) or not os.path.isfile(path):
            continue

        try:
            # Simple text extraction, ignoring heavy binaries or giant minified blocks
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                # Skip files that look like huge minified binaries or are > 1MB
                if len(content) > 1000000:
                    continue
                documents.append(f"--- FILE: {os.path.basename(path)} ---\n{content}\n")
        except Exception:
            continue

    if not documents:
        return "Error: Could not read any of the provided files. Are they valid source code?"

    combined_context = "\n".join(documents)

    payload = {
        "model": SEARCH_MODEL,
        "messages": [
            {"role": "system", "content": DOC_GEN_PROMPT},
            {"role": "user", "content": f"Instructions:\n{instruction}\n\nContext Files:\n{combined_context}"}
        ]
    }

    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            r = await client.post(API_URL, headers=get_headers(), json=payload)
            if r.status_code != 200:
                return f"API Error ({r.status_code}): {r.text}"

            data = r.json()
            doc_content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            if not doc_content:
                return "Error: Model returned empty documentation."

            return doc_content.strip()

        except Exception as e:
            return f"Exception during documentation generation: {str(e)}"

if __name__ == "__main__":
    mcp.run()
