package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/730alchemy/cortex/apps/cortex-tui/internal/config"
	"github.com/730alchemy/cortex/apps/cortex-tui/internal/tui"
	tea "github.com/charmbracelet/bubbletea"
)

func main() {
	// Parse command-line flags
	configPath := flag.String("config", "", "Path to configuration file")
	flag.Parse()

	// Load configuration
	var cfg *config.Config
	var err error

	if *configPath != "" {
		cfg, err = config.Load(*configPath)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Warning: Failed to load config: %v\n", err)
			fmt.Fprintf(os.Stderr, "Using default configuration\n")
			cfg = config.Default()
		}
	} else {
		// Try to load from default locations, fall back to defaults
		cfg, err = config.Load("")
		if err != nil {
			cfg = config.Default()
		}
	}

	// Create TUI model
	m := tui.NewModel(cfg)

	// Run the program
	p := tea.NewProgram(m, tea.WithAltScreen())
	if _, err := p.Run(); err != nil {
		fmt.Fprintf(os.Stderr, "Error running TUI: %v\n", err)
		os.Exit(1)
	}
}
