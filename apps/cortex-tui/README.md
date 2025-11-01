# Cortex TUI

A terminal user interface for interacting with the Cortex knowledge management system.

## Features

- **Query Tab**: Interactive chat interface for querying project knowledge
  - Dedicated project information pane (always visible)
  - Project selection with arrow key navigation (↑/↓)
  - Chat history with collapsible message pairs
  - Real-time query responses
  - Input field for submitting queries

- **Project Tab**: View project information and connected data sources
  - Project metadata display
  - Information sources list (GitHub, Notion, Linear, Google Docs, etc.)
  - Source-specific attribute rendering

## Installation

### Build from Source

```bash
# From the cortex-tui directory
make build

# Or use go directly
go build -o cortex-tui ./cmd/cortex-tui
```

### Install to $GOPATH/bin

```bash
make install
```

## Usage

### Basic Usage

```bash
# Run with default configuration
./bin/cortex-tui

# Or if installed
cortex-tui

# Run with custom config file
cortex-tui -config /path/to/config.toml
```

### Configuration

Create a `cortex-tui.toml` file in the current directory or at `~/.config/cortex/tui.toml`:

```toml
[cortex-api]
url = "http://localhost:8080"
username = ""
password = ""
database = ""

[logging]
level = "info"  # debug, info, warn, error
```

See `cortex-tui.toml.example` for a complete example.

## Keyboard Shortcuts

### Global
- `Tab` / `Shift+Tab`: Switch between tabs
- `q` / `Ctrl+C`: Quit application

### Query Tab
- `↑` / `↓`: Select project
- `Enter`: Submit query
- `Ctrl+↑` / `Ctrl+↓`: Navigate through message history (scrolls to show selected message)
- `Ctrl+K`: Toggle collapse/expand selected message pair
- `Ctrl+L`: Clear chat history

### Project Tab
- `↑` / `↓`: Select project
- `r`: Refresh information sources

## Development

### Prerequisites

- Go 1.21 or later
- Make (optional, but recommended)

### Dependencies

This project uses:
- [Bubble Tea](https://github.com/charmbracelet/bubbletea) - TUI framework
- [Bubbles](https://github.com/charmbracelet/bubbles) - TUI components
- [Lipgloss](https://github.com/charmbracelet/lipgloss) - Terminal styling
- [TOML](https://github.com/BurntSushi/toml) - Configuration parsing

### Development Workflow

```bash
# Format code
make fmt

# Build
make build

# Run
make run

# Development mode (format + build + run)
make dev

# Clean build artifacts
make clean
```

## Architecture

```
apps/cortex-tui/
├── cmd/
│   └── cortex-tui/          # Application entry point
│       └── main.go
├── internal/
│   ├── api/                 # API client (stubbed)
│   │   └── client.go
│   ├── config/              # Configuration loading
│   │   └── config.go
│   ├── models/              # Data models
│   │   └── models.go
│   └── tui/                 # TUI components
│       ├── model.go         # Main application model
│       ├── styles.go        # Styling definitions
│       ├── query.go         # Query tab view
│       ├── project.go       # Project tab view
│       └── logger.go        # Logging support
├── Makefile
├── go.mod
└── README.md
```

## Current Status

**Note**: This is an initial implementation with stubbed API calls. The Cortex API client returns dummy data for demonstration purposes. When the Cortex API gateway is available, the API client in `internal/api/client.go` should be updated to make real HTTP requests.

## Logging

Logs are written to a temporary directory:
- Location: `$TMPDIR/cortex-tui/cortex-tui.log` (typically `/tmp/cortex-tui/cortex-tui.log`)
- Level configurable via `logging.level` in config file
- Levels: `debug`, `info`, `warn`, `error`

## License

See the main repository LICENSE file.
