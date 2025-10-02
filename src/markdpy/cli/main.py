"""CLI main entry point using Typer."""

import time
import webbrowser
from pathlib import Path

import typer
import uvicorn
from rich.console import Console

from markdpy import __version__
from markdpy.config.models import VALID_THEMES, ServerConfig
from markdpy.config.settings import DEFAULT_HOST, DEFAULT_PORT, DEFAULT_THEME
from markdpy.telemetry import flush, init_telemetry, track_error

app = typer.Typer(
    name="markdpy",
    help="Python-based Markdown preview server with live reload",
    add_completion=False,
)

console = Console()


@app.command()
def serve(
    path: Path = typer.Argument(
        Path("."),
        help="Path to Markdown file or directory to serve",
        exists=True,
    ),
    port: int = typer.Option(
        DEFAULT_PORT,
        "--port",
        "-p",
        help="Port to bind server (1024-65535)",
        min=1024,
        max=65535,
    ),
    host: str = typer.Option(
        DEFAULT_HOST,
        "--host",
        "-h",
        help="Host to bind server",
    ),
    theme: str = typer.Option(
        DEFAULT_THEME,
        "--theme",
        "-t",
        help=f"UI theme ({'/'.join(VALID_THEMES)})",
    ),
    no_open: bool = typer.Option(
        False,
        "--no-open",
        help="Don't open browser automatically",
    ),
    no_reload: bool = typer.Option(
        False,
        "--no-reload",
        help="Disable live reload",
    ),
    no_telemetry: bool = typer.Option(
        False,
        "--no-telemetry",
        help="Disable telemetry",
    ),
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        "--log",
        "-l",
        help="Logging level (DEBUG/INFO/WARNING/ERROR)",
    ),
) -> None:
    """Start the Markdown preview server."""
    try:
        # Validate path
        if not path.exists():
            console.print(f"[red]✗[/red] Path not found: {path}", style="bold")
            raise typer.Exit(code=3)

        # Create server config
        config = ServerConfig(
            host=host,
            port=port,
            serve_path=path.absolute(),
            theme=theme,
            open_browser=not no_open,
            reload_enabled=not no_reload,
            allow_write=False,
            log_level=log_level,
            telemetry_enabled=not no_telemetry,
        )

        # Validate config
        try:
            config.validate()
        except ValueError as e:
            console.print(f"[red]✗[/red] Configuration error: {e}", style="bold")
            raise typer.Exit(code=2)

        # Import and display banner
        from markdpy.server.banner import print_banner

        print_banner(
            host=host,
            port=port,
            serve_path=config.serve_path,
            theme=config.theme,
            reload_enabled=config.reload_enabled,
            telemetry_enabled=config.telemetry_enabled,
        )

        # Open browser if requested
        if config.open_browser:
            import threading
            import time

            def open_browser_delayed():
                time.sleep(1.5)  # Wait for server to start
                webbrowser.open(f"http://{host}:{port}")

            threading.Thread(target=open_browser_delayed, daemon=True).start()

        # Create app with config
        from markdpy.server.app import create_app

        server_app = create_app(config)

        # Start server
        uvicorn.run(
            server_app,
            host=host,
            port=port,
            log_level=log_level.lower(),
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped[/yellow]")
        raise typer.Exit(code=0)
    except OSError as e:
        if "address already in use" in str(e).lower():
            console.print(f"[red]✗[/red] Port {port} is already in use", style="bold")
            raise typer.Exit(code=5)
        console.print(f"[red]✗[/red] Error: {e}", style="bold")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}", style="bold")
        raise typer.Exit(code=1)


@app.command()
def export(
    source: Path = typer.Argument(
        ...,
        help="Source Markdown file or directory",
        exists=True,
    ),
    output: Path = typer.Argument(
        Path("output"),
        help="Output directory for exported HTML",
    ),
    theme: str = typer.Option(
        DEFAULT_THEME,
        "--theme",
        "-t",
        help=f"Theme for exported HTML ({'/'.join(VALID_THEMES)})",
    ),
    minify: bool = typer.Option(
        False,
        "--minify",
        help="Minify exported HTML",
    ),
) -> None:
    """Export Markdown to static HTML files."""
    # Initialize telemetry for CLI usage
    init_telemetry(__version__)
    start_time = time.time()

    try:
        # Validate source path
        if not source.exists():
            track_error()  # Track validation error
            console.print(f"[red]✗[/red] Source not found: {source}", style="bold")
            raise typer.Exit(code=3)

        # Create exporter
        from markdpy.exporter import StaticSiteGenerator

        generator = StaticSiteGenerator(theme=theme, minify=minify)

        console.print("\n[bold blue]markdpy export[/bold blue] - Static HTML Generator\n")
        console.print(f"[green]✓[/green] Source: {source}")
        console.print(f"[green]✓[/green] Output: {output}")
        console.print(f"[green]✓[/green] Theme: {theme}")
        console.print(f"[green]✓[/green] Minify: {'yes' if minify else 'no'}\n")

        # Export based on source type
        if source.is_file():
            # Single file export
            exported = generator.export_file(source, output)
            console.print(f"[green]✓[/green] Exported: {exported.relative_to(output.absolute())}")
        else:
            # Directory export
            exported_files = generator.export_directory(source, output, recursive=True)
            console.print(f"[green]✓[/green] Exported {len(exported_files)} files\n")

            for file in exported_files[:10]:  # Show first 10
                console.print(f"  • {file.relative_to(output.absolute())}")

            if len(exported_files) > 10:
                console.print(f"  ... and {len(exported_files) - 10} more\n")

        console.print(f"\n[bold green]Export complete![/bold green] Output: {output.absolute()}\n")

        # Track successful export
        export_time_ms = (time.time() - start_time) * 1000
        from markdpy.telemetry import track_render

        track_render(export_time_ms)  # Reuse render tracking for export operations

    except FileNotFoundError as e:
        track_error()  # Track file not found error
        console.print(f"[red]✗[/red] {e}", style="bold")
        raise typer.Exit(code=3)
    except ValueError as e:
        track_error()  # Track validation error
        console.print(f"[red]✗[/red] {e}", style="bold")
        raise typer.Exit(code=2)
    except Exception as e:
        track_error()  # Track any other error
        console.print(f"[red]✗[/red] Error: {e}", style="bold")
        raise typer.Exit(code=1)
    finally:
        # Ensure telemetry is flushed before CLI exits
        flush()


def main() -> None:
    """Main entry point."""
    # Create factory function that uvicorn can call
    global _config
    _config = None

    def create_app_factory() -> "fastapi.FastAPI":  # type: ignore # noqa: F821
        from markdpy.server.app import create_app

        return create_app(_config) if _config else create_app(ServerConfig())

    app()


if __name__ == "__main__":
    main()
