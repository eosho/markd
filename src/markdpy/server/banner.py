"""Banner display utilities for markdpy CLI."""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


BANNER = """
 ███╗   ███╗ █████╗ ██████╗ ██╗  ██╗██████╗ ██████╗ ██╗   ██╗
 ████╗ ████║██╔══██╗██╔══██╗██║ ██╔╝██╔══██╗██╔══██╗╚██╗ ██╔╝
 ██╔████╔██║███████║██████╔╝█████╔╝ ██║  ██║██████╔╝ ╚████╔╝
 ██║╚██╔╝██║██╔══██║██╔══██╗██╔═██╗ ██║  ██║██╔═══╝   ╚██╔╝
 ██║ ╚═╝ ██║██║  ██║██║  ██║██║  ██╗██████╔╝██║        ██║
 ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝        ╚═╝
"""

TAGLINE = "Python-based Markdown Preview Server with Live Reload"


def print_banner(
    host: str,
    port: int,
    serve_path: Path,
    theme: str,
    reload_enabled: bool = True,
    telemetry_enabled: bool = True,
) -> None:
    """Display the ASCII art banner with server information.

    Args:
        host: Server host address
        port: Server port number
        serve_path: Path being served
        theme: Active theme name
        reload_enabled: Whether live reload is enabled
        telemetry_enabled: Whether telemetry is enabled
    """
    # Create gradient effect with different colors
    banner_lines = BANNER.strip().split("\n")
    colors = ["bright_blue", "blue", "cyan", "bright_cyan", "magenta", "bright_magenta"]

    styled_banner = Text()
    for i, line in enumerate(banner_lines):
        color = colors[i % len(colors)]
        styled_banner.append(line + "\n", style=color)

    console.print()
    console.print(styled_banner)
    console.print(Text(TAGLINE, style="italic bright_yellow bold"))
    console.print()

    # Server information in a styled panel
    info_content = Text()
    info_content.append("🌐 ", style="bright_white")
    info_content.append("Server:      ", style="dim")
    info_content.append(f"http://{host}:{port}", style="bright_green bold")
    info_content.append("\n")

    info_content.append("🔗 ", style="bright_white")
    info_content.append("Debugging:   ", style="dim")
    info_content.append(f"http://{host}:{port}/raw", style="bright_green bold")
    info_content.append("\n")

    info_content.append("📂 ", style="bright_white")
    info_content.append("Serving:     ", style="dim")
    info_content.append(str(serve_path), style="bright_blue")
    info_content.append("\n")

    info_content.append("🎨 ", style="bright_white")
    info_content.append("Theme:       ", style="dim")
    info_content.append(theme, style="bright_magenta")
    info_content.append("\n")

    info_content.append("🔄 ", style="bright_white")
    info_content.append("Live Reload: ", style="dim")
    reload_status = "enabled" if reload_enabled else "disabled"
    reload_style = "bright_cyan bold" if reload_enabled else "yellow"
    info_content.append(reload_status, style=reload_style)
    info_content.append("\n")

    info_content.append("📊 ", style="bright_white")
    info_content.append("Telemetry:   ", style="dim")
    telemetry_status = "enabled" if telemetry_enabled else "disabled"
    telemetry_style = "bright_cyan bold" if telemetry_enabled else "yellow"
    info_content.append(telemetry_status, style=telemetry_style)

    console.print(
        Panel(
            info_content,
            title="[bold bright_white]Server Configuration[/bold bright_white]",
            border_style="bright_cyan",
            padding=(1, 2),
            expand=False,
        )
    )
    console.print()
    console.print("  [dim italic]Press Ctrl+C to stop the server[/dim italic]")
    console.print()
