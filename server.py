"""
ViralVadoo MCP Server

Exposes all Vadoo AI APIs as MCP tools, compatible with:
  - Claude Desktop
  - Claude Code
  - Cursor
  - ChatGPT (via OpenAI-compatible MCP bridge)

Usage:
  python server.py

Then register in your MCP client — see README.md for per-client setup.
"""

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from dotenv import load_dotenv

import vadoo_client as vc

load_dotenv()

app = Server("viradvadoo-mcp")

# ─────────────────────────────────────────────────────────────────────────────
# Tool definitions
# ─────────────────────────────────────────────────────────────────────────────

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        # ── Account ──────────────────────────────────────────────────────────
        types.Tool(
            name="get_balance",
            description=(
                "Get your current Vadoo AI credit balance. "
                "Credits are shared across all services."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),

        # ── AI Story / Video ──────────────────────────────────────────────────
        types.Tool(
            name="generate_video",
            description=(
                "Generate a high-quality AI short video from a topic, a custom script, "
                "or a blog/article URL. Returns a vid (video ID) for status polling."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": (
                            "Topic of the video (e.g. 'Motivational', 'Horror Story', "
                            "'Custom'). Use 'Custom' with the prompt field for your own script."
                        ),
                    },
                    "prompt": {
                        "type": "string",
                        "description": (
                            "Required when topic='Custom'. The story prompt or exact script. "
                            "Max chars: 1000 (30-60s), 1500 (60-90s), 2000 (90-120s), "
                            "2500 (120-180s), 5000 (5 min), 10000 (10 min)."
                        ),
                    },
                    "duration": {
                        "type": "string",
                        "enum": ["30-60", "60-90", "90-120", "120-180", "5 min", "10 min"],
                        "description": "Target video duration. Default: '30-60'.",
                    },
                    "voice": {
                        "type": "string",
                        "description": "AI voice name (e.g. Onyx, Nova, Shimmer). Default: Onyx.",
                    },
                    "language": {
                        "type": "string",
                        "description": "Language for the video. Default: English.",
                    },
                    "aspect_ratio": {
                        "type": "string",
                        "enum": ["9:16", "1:1", "16:9"],
                        "description": "Video aspect ratio. Default: 9:16.",
                    },
                    "style": {
                        "type": "string",
                        "description": (
                            "Visual style (e.g. 'cinematic', 'anime', 'watercolor'). "
                            "Use list_styles to see all options."
                        ),
                    },
                    "theme": {
                        "type": "string",
                        "description": (
                            "Caption theme name (e.g. Hormozi_1, Beast). "
                            "Use list_themes to see all options. Default: Hormozi_1."
                        ),
                    },
                    "bg_music": {
                        "type": "string",
                        "description": "Background music track name.",
                    },
                    "bg_music_volume": {
                        "type": "number",
                        "description": "Volume for background music (0-100). Default: 100.",
                    },
                    "speed": {
                        "type": "number",
                        "description": "Voiceover playback speed (0.5–2.0). Default: 1.0.",
                    },
                    "use_ai": {
                        "type": "integer",
                        "enum": [0, 1],
                        "description": (
                            "1 = AI generates the script from prompt as a guideline (default). "
                            "0 = use prompt as the exact verbatim voiceover script."
                        ),
                    },
                    "include_voiceover": {
                        "type": "integer",
                        "enum": [0, 1],
                        "description": "1 = include voiceover (default), 0 = no voiceover.",
                    },
                    "custom_instructions": {
                        "type": "string",
                        "description": "Additional creative instructions for the AI.",
                    },
                    "url": {
                        "type": "string",
                        "description": "Blog/article URL to convert into a video.",
                    },
                    "webhook": {
                        "type": "string",
                        "description": "Optional webhook URL to receive completion notification.",
                    },
                },
                "required": [],
            },
        ),

        types.Tool(
            name="get_video_status",
            description=(
                "Poll the status of a video generation task. "
                "Returns status ('processing'|'completed'|'failed'), progress %, and URL when done."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "The vid or request_id returned by a generation endpoint.",
                    }
                },
                "required": ["id"],
            },
        ),

        # ── AI Captions ───────────────────────────────────────────────────────
        types.Tool(
            name="add_captions",
            description=(
                "Add AI-generated captions/subtitles to a video. "
                "Returns a vid for status polling. Max 600 MB / 10 minutes."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Public URL of the video to caption.",
                    },
                    "language": {
                        "type": "string",
                        "description": "Language of the video. Default: English.",
                    },
                    "theme": {
                        "type": "string",
                        "description": "Caption theme (e.g. Hormozi_1, Beast). Default: Hormozi_1.",
                    },
                    "webhook": {
                        "type": "string",
                        "description": "Optional webhook URL for completion notification.",
                    },
                },
                "required": ["url"],
            },
        ),

        # ── AI Clips ──────────────────────────────────────────────────────────
        types.Tool(
            name="create_ai_clips",
            description=(
                "Extract the most viral short-form clips from a long video (YouTube or MP4 URL) "
                "with AI-powered framing and subtitles. Returns a request_id for polling."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "video_url": {
                        "type": "string",
                        "description": "URL of the source long-form video (YouTube or direct MP4).",
                    },
                    "num_highlights": {
                        "type": "integer",
                        "description": "Number of viral clips to extract. Default: 3.",
                    },
                    "aspect_ratio": {
                        "type": "string",
                        "enum": ["9:16", "1:1", "16:9"],
                        "description": "Target aspect ratio. Default: 9:16.",
                    },
                    "return_coordinates_only": {
                        "type": "boolean",
                        "description": (
                            "If true, returns only bounding-box coordinates without rendering. "
                            "Default: false."
                        ),
                    },
                    "webhook": {
                        "type": "string",
                        "description": "Optional webhook URL for completion notification.",
                    },
                },
                "required": ["video_url"],
            },
        ),

        # ── AI Podcast ────────────────────────────────────────────────────────
        types.Tool(
            name="generate_podcast",
            description=(
                "Generate a 2-person AI podcast from a blog URL, PDF link, or raw text. "
                "Returns a vid for status polling."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL of a blog post or PDF. Required if text not provided.",
                    },
                    "text": {
                        "type": "string",
                        "description": "Raw text or transcript. Required if url not provided.",
                    },
                    "name1": {
                        "type": "string",
                        "description": "Name of the first speaker.",
                    },
                    "name2": {
                        "type": "string",
                        "description": "Name of the second speaker.",
                    },
                    "voice1": {
                        "type": "string",
                        "description": "Voice for speaker 1. Default: Onyx.",
                    },
                    "voice2": {
                        "type": "string",
                        "description": "Voice for speaker 2. Default: Alloy.",
                    },
                    "language": {
                        "type": "string",
                        "description": "Podcast language. Default: English.",
                    },
                    "duration": {
                        "type": "string",
                        "enum": ["1-2", "2-5"],
                        "description": "'1-2' for short, '2-5' for long-form. Default: 1-2.",
                    },
                    "tone": {
                        "type": "string",
                        "description": "Conversation tone (e.g. Friendly, Professional, Funny). Default: Friendly.",
                    },
                    "theme": {
                        "type": "string",
                        "description": "Caption theme. Default: Hormozi_1.",
                    },
                    "webhook": {
                        "type": "string",
                        "description": "Optional webhook URL for completion notification.",
                    },
                },
                "required": ["name1", "name2"],
            },
        ),

        # ── AI Character ──────────────────────────────────────────────────────
        types.Tool(
            name="list_characters",
            description="List all AI characters you have created or saved in your Vadoo account.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),

        types.Tool(
            name="generate_character_image",
            description=(
                "Generate a new image of an existing AI character in a custom scene or pose. "
                "Returns an id for status polling via get_character_image_status."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "ID of the AI Character (from list_characters).",
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Description of the scene or character pose.",
                    },
                    "ratio": {
                        "type": "string",
                        "enum": ["1:1", "3:4", "4:3", "16:9", "9:16"],
                        "description": "Aspect ratio of the generated image.",
                    },
                },
                "required": ["id", "prompt", "ratio"],
            },
        ),

        types.Tool(
            name="get_character_image_status",
            description=(
                "Poll the status of a character image generation task. "
                "Returns status and URL when completed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "The image ID returned by generate_character_image.",
                    }
                },
                "required": ["id"],
            },
        ),

        # ── Discovery / Listing ───────────────────────────────────────────────
        types.Tool(
            name="list_voices",
            description="List all available AI voices for video and podcast generation.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),

        types.Tool(
            name="list_languages",
            description="List all supported languages for video, captions, and podcast generation.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),

        types.Tool(
            name="list_styles",
            description="List all available visual image styles for AI video generation.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),

        types.Tool(
            name="list_themes",
            description="List all available caption/subtitle themes and their configurations.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),

        types.Tool(
            name="list_video_topics",
            description="List all available predefined video topic categories.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),

        types.Tool(
            name="list_background_music",
            description="List all available background music tracks for AI video generation.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Tool call dispatcher
# ─────────────────────────────────────────────────────────────────────────────

def _ok(data: Any) -> list[types.TextContent]:
    """Wrap a successful result as pretty-printed JSON text."""
    return [types.TextContent(type="text", text=json.dumps(data, indent=2))]


def _err(msg: str) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=f"Error: {msg}")]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    try:
        # ── Account ──────────────────────────────────────────────────────────
        if name == "get_balance":
            return _ok(await vc.get("/api/get_my_balance"))

        # ── AI Video ─────────────────────────────────────────────────────────
        elif name == "generate_video":
            return _ok(await vc.post("/api/generate_video", arguments))

        elif name == "get_video_status":
            return _ok(await vc.get("/api/get_video_url", {"id": arguments["id"]}))

        # ── Captions ─────────────────────────────────────────────────────────
        elif name == "add_captions":
            return _ok(await vc.post("/api/add_captions", arguments))

        # ── Clips ────────────────────────────────────────────────────────────
        elif name == "create_ai_clips":
            return _ok(await vc.post("/api/create_ai_clips", arguments))

        # ── Podcast ──────────────────────────────────────────────────────────
        elif name == "generate_podcast":
            return _ok(await vc.post("/api/generate_podcast", arguments))

        # ── Characters ───────────────────────────────────────────────────────
        elif name == "list_characters":
            return _ok(await vc.get("/api/get_all_characters"))

        elif name == "generate_character_image":
            return _ok(await vc.post("/api/generate_character_image", arguments))

        elif name == "get_character_image_status":
            return _ok(await vc.get("/api/get_character_image", {"id": arguments["id"]}))

        # ── Discovery ────────────────────────────────────────────────────────
        elif name == "list_voices":
            return _ok(await vc.get("/api/get_voices"))

        elif name == "list_languages":
            return _ok(await vc.get("/api/get_languages"))

        elif name == "list_styles":
            return _ok(await vc.get("/api/get_styles"))

        elif name == "list_themes":
            return _ok(await vc.get("/api/get_themes"))

        elif name == "list_video_topics":
            return _ok(await vc.get("/api/get_topics"))

        elif name == "list_background_music":
            return _ok(await vc.get("/api/get_background_music"))

        else:
            return _err(f"Unknown tool: {name}")

    except ValueError as exc:
        return _err(str(exc))
    except Exception as exc:  # noqa: BLE001
        return _err(f"API request failed: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
