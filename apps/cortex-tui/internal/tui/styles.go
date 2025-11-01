package tui

import "github.com/charmbracelet/lipgloss"

var (
	// Colors
	colorPrimary   = lipgloss.Color("86")  // Cyan
	colorSecondary = lipgloss.Color("212") // Pink
	colorMuted     = lipgloss.Color("241") // Gray
	colorAccent    = lipgloss.Color("220") // Yellow
	colorError     = lipgloss.Color("196") // Red
	colorSuccess   = lipgloss.Color("42")  // Green

	// Tab styles
	styleActiveTab = lipgloss.NewStyle().
			Bold(true).
			Foreground(colorPrimary).
			Background(lipgloss.Color("235")).
			Padding(0, 2)

	styleInactiveTab = lipgloss.NewStyle().
				Foreground(colorMuted).
				Padding(0, 2)

	// Header styles
	styleHeader = lipgloss.NewStyle().
			Bold(true).
			Foreground(colorPrimary).
			MarginBottom(1)

	styleSubHeader = lipgloss.NewStyle().
			Foreground(colorSecondary).
			MarginBottom(1)

	styleProjectName = lipgloss.NewStyle().
				Foreground(colorSecondary).
				Bold(true)

	// Message styles
	styleUserMessage = lipgloss.NewStyle().
				Foreground(colorAccent).
				Bold(true).
				MarginBottom(1)

	styleAssistantMessage = lipgloss.NewStyle().
				Foreground(lipgloss.Color("255")).
				MarginBottom(1)

	styleTimestamp = lipgloss.NewStyle().
			Foreground(colorMuted).
			Italic(true)

	// Input styles
	styleInput = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(colorPrimary).
			Padding(0, 1)

	styleInputPrompt = lipgloss.NewStyle().
				Foreground(colorPrimary).
				Bold(true)

	// List styles
	styleListItem = lipgloss.NewStyle().
			Foreground(lipgloss.Color("255")).
			MarginLeft(2)

	styleSelectedItem = lipgloss.NewStyle().
				Foreground(colorPrimary).
				Bold(true).
				MarginLeft(2)

	// Source type styles
	styleSourceType = lipgloss.NewStyle().
			Foreground(colorSecondary).
			Bold(true)

	styleSourceName = lipgloss.NewStyle().
			Foreground(colorPrimary)

	styleSourceAttr = lipgloss.NewStyle().
			Foreground(colorMuted)

	// Status styles
	styleLoading = lipgloss.NewStyle().
			Foreground(colorAccent).
			Italic(true)

	styleError = lipgloss.NewStyle().
			Foreground(colorError).
			Bold(true)

	styleSuccess = lipgloss.NewStyle().
			Foreground(colorSuccess)

	// Help text
	styleHelp = lipgloss.NewStyle().
			Foreground(colorMuted).
			Italic(true).
			MarginTop(1)

	// Container styles
	styleBox = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(colorMuted).
			Padding(1, 2)

	styleScrollableBox = lipgloss.NewStyle().
				Border(lipgloss.RoundedBorder()).
				BorderForeground(colorPrimary).
				Padding(1, 2)
)
