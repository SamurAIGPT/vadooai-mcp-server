# ViralVadoo MCP Server

An MCP (Model Context Protocol) server that exposes all **Vadoo AI** APIs as tools — compatible with **Claude Desktop, Claude Code, Cursor, and ChatGPT**.

## Tools Available

| Tool                         | Description                                                 |
| ---------------------------- | ----------------------------------------------------------- |
| `get_balance`                | Check your remaining credit balance                         |
| `generate_video`             | Create an AI video from a topic, custom script, or blog URL |
| `get_video_status`           | Poll video generation progress and get the final URL        |
| `add_captions`               | Add AI captions/subtitles to any video                      |
| `create_ai_clips`            | Extract viral short clips from a long YouTube/MP4 video     |
| `generate_podcast`           | Generate a 2-person AI podcast from a URL, PDF, or text     |
| `list_characters`            | List your AI characters                                     |
| `generate_character_image`   | Generate a new image of an AI character                     |
| `get_character_image_status` | Poll character image generation status                      |
| `list_voices`                | List all available AI voices                                |
| `list_languages`             | List supported languages                                    |
| `list_styles`                | List available visual image styles                          |
| `list_themes`                | List available caption themes                               |
| `list_video_topics`          | List predefined video topic categories                      |
| `list_background_music`      | List available background music tracks                      |

---

## Setup

### 1. Install dependencies

```bash
cd ViralVadoo/mcp-server
pip install -r requirements.txt
```

### 2. Set your API key

```bash
cp .env.example .env
# Edit .env and add your Vadoo API key
# Get your key at: https://ai.vadoo.tv/profile
```

---

## Client Configuration

### Claude Desktop

Edit `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "viradvadoo": {
      "command": "python",
      "args": ["C:\\path\\to\\ViralVadoo\\mcp-server\\server.py"],
      "env": {
        "VADOO_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

> **Tip:** Use the full absolute path to `server.py`. Alternatively, store the key in `.env` and omit the `env` block.

---

### Claude Code

Run from the terminal inside the `mcp-server` directory:

```bash
claude mcp add viradvadoo -- python /full/path/to/server.py
```

Or set the env variable first:

```bash
VADOO_API_KEY=your_key claude mcp add viradvadoo -- python /full/path/to/server.py
```

Verify it is registered:

```bash
claude mcp list
```

---

### Cursor

Open **Settings → MCP** and add a new server entry:

```json
{
  "viradvadoo": {
    "command": "python",
    "args": ["/full/path/to/ViralVadoo/mcp-server/server.py"],
    "env": {
      "VADOO_API_KEY": "your_api_key_here"
    }
  }
}
```

---

### ChatGPT (OpenAI)

### ChatGPT (via mcp-proxy HTTP bridge)

Since ChatGPT runs in the cloud, it cannot run local python files directly. We can bridge this local `stdio` server to `SSE` (HTTP) and tunnel it.

1. Install `mcp-proxy`:
```cmd
pip install mcp-proxy
```

2. Run the proxy with your API key:

**Windows Command Prompt (CMD):**
```cmd
set VADOO_API_KEY=your_key_here && mcp-proxy --port 8080 -- python "C:\Users\JAYAP\joint-folder\ViralVadoo\mcp-server\server.py"
```

**PowerShell:**
```powershell
$env:VADOO_API_KEY="your_key_here"; mcp-proxy --port 8080 -- python "C:\Users\JAYAP\joint-folder\ViralVadoo\mcp-server\server.py"
```

3. Expose your port 8080 using `ngrok` or `localtunnel` so ChatGPT can connect to it:
```cmd
npx localtunnel --port 8080
```
Copy the forwarding URL (e.g., `https://xxxx.localtunnel.me`).

4. Add to ChatGPT:
   - Go to **ChatGPT Settings** → **Apps** / **Connectors** → **Developer Mode** (Turn ON).
   - Click **Add MCP Server** / **Add App**.
   - Set URL to your tunnel URL with `/sse` appended (e.g. `https://xxxx.localtunnel.me/sse`).


---

## Quick Test

```bash
# Start the server directly (stdin/stdout MCP protocol)
python server.py
```

The server is ready when it silently awaits — connect your MCP client and the tools will appear automatically.
