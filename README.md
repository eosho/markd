```
 ███╗   ███╗ █████╗ ██████╗ ██╗  ██╗██████╗ ██████╗ ██╗   ██╗
 ████╗ ████║██╔══██╗██╔══██╗██║ ██╔╝██╔══██╗██╔══██╗╚██╗ ██╔╝
 ██╔████╔██║███████║██████╔╝█████╔╝ ██║  ██║██████╔╝ ╚████╔╝
 ██║╚██╔╝██║██╔══██║██╔══██╗██╔═██╗ ██║  ██║██╔═══╝   ╚██╔╝
 ██║ ╚═╝ ██║██║  ██║██║  ██║██║  ██╗██████╔╝██║        ██║
 ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝        ╚═╝
```

## markdpy - markdown in python

Python-based markdown preview server with live reload, themes, diagrams, and static export capabilities.

[![GitHub Release](https://img.shields.io/github/v/release/eosho/markdpy?sytle=flat&label=Release&labelColor=black&color=%237B2CBF)](https://github.com/eosho/markdpy/releases)
[![GitHub License](https://img.shields.io/github/license/eosho/markdpy?style=flat&label=License&labelColor=black&color=%237B2CBF)](LICENSE)
[![GitHub Repo stars](https://img.shields.io/github/stars/eosho/markdpy?style=flat&logo=github&logoColor=white&label=Stars&labelColor=black&color=7B2CBF)](https://github.com/eosho/markdpy)


## ✨ Features

- 🔄 **Live Reload**: Automatic browser refresh on file changes with WebSocket
- 🎨 **Multiple Themes**: Light and dark themes with smooth toggle
- 📊 **Mermaid Diagrams**: Render flowcharts, sequence diagrams, and more
- 📐 **MathJax Support**: Beautiful mathematical formulas (KaTeX-ready)
- 📁 **Directory Navigation**: Browse multiple markdown files with sidebar
- 📤 **Static Export**: Generate self-contained HTML for sharing
- 🔒 **Secure by Default**: Directory traversal prevention, CSP headers
- ⚡ **Fast**: <100ms rendering, <200ms reload latency
- 🌐 **Cross-Platform**: Works on Linux, macOS, and Windows

## 📦 Installation

### From PyPI (Recommended)

```bash
pip install markdpy
```

### From Source

```bash
git clone https://github.com/eosho/markdpy.git
cd markdpy
pip install -e .
```

## 🚀 Quick Start

### Serve a Single File

The simplest way to preview a markdown file:

```bash
markdpy README.md
```

This will:
- Start the server on `http://127.0.0.1:8000`
- Open your default browser automatically
- Enable live reload (changes refresh the browser)

### Serve a Directory

Preview all markdown files in a directory with navigation:

```bash
markdpy docs/
```

Features:
- Sidebar navigation with all `.md` files
- Automatic index detection (index.md, README.md)
- Directory browsing support

### Custom Configuration

```bash
markdpy docs/ --port 3000 --theme dark --no-open
```

## 📖 Detailed Usage

### `serve` Command

Start a markdown preview server.

```bash
markdpy serve [PATH] [OPTIONS]
```

#### Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `PATH` | Path | `.` (current directory) | Path to markdown file or directory to serve |

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--port` | `-p` | Integer | `8000` | Port to bind server (1024-65535) |
| `--host` | `-h` | String | `127.0.0.1` | Host address to bind server |
| `--theme` | `-t` | Choice | `light` | UI theme: `light` or `dark` |
| `--no-open` | | Flag | `False` | Don't open browser automatically |
| `--no-reload` | | Flag | `False` | Disable live reload (WebSocket) |
| `--log-level` | | Choice | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

#### Examples

**Serve with custom port:**
```bash
markdpy docs/ --port 3000
```

**Dark theme without auto-opening:**
```bash
markdpy README.md --theme dark --no-open
```

**Debug mode with live reload disabled:**
```bash
markdpy docs/ --log-level DEBUG --no-reload
```

**Bind to all interfaces (accessible from network):**
```bash
markdpy docs/ --host 0.0.0.0 --port 8080
```

### `export` Command

Export markdown to static HTML files.

```bash
markdpy export SOURCE [OUTPUT] [OPTIONS]
```

#### Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `SOURCE` | Path | **Required** | Source markdown file or directory |
| `OUTPUT` | Path | `output` | Output directory for exported HTML |

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--theme` | `-t` | Choice | `light` | Theme for exported HTML: `light` or `dark` |
| `--minify` | | Flag | `False` | Minify exported HTML (reduces file size) |

#### Examples

**Export single file:**
```bash
markdpy export README.md output/
```

**Export directory with dark theme:**
```bash
markdpy export docs/ site/ --theme dark
```

**Export with minification:**
```bash
markdpy export docs/ site/ --minify
```

## 📝 Supported markdown Features

### GitHub Flavored markdown (GFM)

- **Tables**: Full table support with alignment
- **Task Lists**: `- [ ]` and `- [x]` checkboxes
- **Strikethrough**: `~~deleted text~~`
- **Autolinks**: Automatic URL detection

### Code Blocks

Syntax highlighting for 100+ languages using Pygments:

```python
def hello_world():
    print("Hello from markdpy!")
```

### Mermaid Diagrams

```mermaid
graph LR
    A[Start] --> B[Process]
    B --> C[End]
```

Supported diagram types:
- Flowcharts
- Sequence diagrams
- Class diagrams
- State diagrams
- Gantt charts
- Pie charts

### Mathematical Expressions

Inline math: `$E = mc^2$`

Block math:

$$
\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}
$$

## 🔧 Configuration

### Server Configuration

Configure via command-line options or environment variables:

| Setting | CLI Option | Environment Variable | Default |
|---------|------------|---------------------|---------|
| Host | `--host` | `HOST` | `127.0.0.1` |
| Port | `--port` | `PORT` | `8000` |
| Theme | `--theme` | `THEME` | `light` |
| Log Level | `--log-level` | `LOG_LEVEL` | `INFO` |### Browser Configuration

Themes are stored in browser `localStorage`:
- Key: `markdpy-theme`
- Values: `light` | `dark`

## 🧪 Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/eosho/markdpy.git
cd markdpy

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/markdpy --cov-report=html

# Run specific test file
pytest tests/integration/test_http_view.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Error: Port 8000 is already in use
markdpy README.md --port 8080
```

### Live Reload Not Working

1. Check that `--no-reload` is not set
2. Verify WebSocket connection in browser console (F12)
3. Check firewall settings
4. Try `--log-level DEBUG` for detailed logs

### Theme Not Loading

1. Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)
2. Check browser console for CSS loading errors
3. Verify `src/markdpy/static/css/themes/` directory exists

### Mermaid Diagrams Not Rendering

1. Ensure CDN is accessible (requires internet connection)
2. Check browser console for JavaScript errors
3. Verify diagram syntax at [mermaid.live](https://mermaid.live)

---

**Made with ❤️ by the markdpy team**
