package config

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/BurntSushi/toml"
)

// Config represents the application configuration
type Config struct {
	CortexAPI CortexAPIConfig `toml:"cortex-api"`
	Logging   LoggingConfig   `toml:"logging"`
}

// CortexAPIConfig contains Cortex API connection settings
type CortexAPIConfig struct {
	URL      string `toml:"url"`
	Username string `toml:"username"`
	Password string `toml:"password"`
	Database string `toml:"database"`
}

// LoggingConfig contains logging settings
type LoggingConfig struct {
	Level string `toml:"level"`
}

// Load reads the configuration from a TOML file
func Load(configPath string) (*Config, error) {
	var cfg Config

	// If no path specified, try default locations
	if configPath == "" {
		configPath = findDefaultConfig()
	}

	// Read the file
	data, err := os.ReadFile(configPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read config file: %w", err)
	}

	// Parse TOML
	if err := toml.Unmarshal(data, &cfg); err != nil {
		return nil, fmt.Errorf("failed to parse config: %w", err)
	}

	// Apply defaults
	if cfg.Logging.Level == "" {
		cfg.Logging.Level = "info"
	}

	return &cfg, nil
}

// findDefaultConfig looks for config in common locations
func findDefaultConfig() string {
	// Try current directory
	if _, err := os.Stat("cortex-tui.toml"); err == nil {
		return "cortex-tui.toml"
	}

	// Try home directory
	home, err := os.UserHomeDir()
	if err == nil {
		configPath := filepath.Join(home, ".config", "cortex", "tui.toml")
		if _, err := os.Stat(configPath); err == nil {
			return configPath
		}
	}

	// Return default path (will fail if not exists)
	return "cortex-tui.toml"
}

// Default returns a default configuration (for when no config file exists)
func Default() *Config {
	return &Config{
		CortexAPI: CortexAPIConfig{
			URL:      "http://localhost:8080",
			Username: "",
			Password: "",
			Database: "",
		},
		Logging: LoggingConfig{
			Level: "info",
		},
	}
}
