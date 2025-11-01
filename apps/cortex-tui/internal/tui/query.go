package tui

import (
	"strings"
	"time"

	"github.com/730alchemy/cortex/apps/cortex-tui/internal/models"
	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
)

// QueryView represents the Query tab
type QueryView struct {
	model     *Model
	textInput textinput.Model
	viewport  int // scroll position in message history
}

// NewQueryView creates a new Query view
func NewQueryView(m *Model) *QueryView {
	ti := textinput.New()
	ti.Placeholder = "Ask a question about your project..."
	ti.Focus()
	ti.CharLimit = 500
	ti.Width = 80

	return &QueryView{
		model:     m,
		textInput: ti,
		viewport:  0,
	}
}

// Update handles updates for the Query view
func (qv *QueryView) Update(msg tea.Msg) tea.Cmd {
	var cmd tea.Cmd

	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "enter":
			// Submit query if not empty
			if strings.TrimSpace(qv.textInput.Value()) != "" {
				return qv.submitQuery()
			}
			return nil

		case "up":
			// Navigate project selector
			if qv.model.selectedProject > 0 {
				qv.model.selectedProject--
				projectID := qv.model.projects[qv.model.selectedProject].ID
				return qv.model.loadInfoSources(projectID)
			}
			return nil

		case "down":
			// Navigate project selector
			if qv.model.selectedProject < len(qv.model.projects)-1 {
				qv.model.selectedProject++
				projectID := qv.model.projects[qv.model.selectedProject].ID
				return qv.model.loadInfoSources(projectID)
			}
			return nil

		case "ctrl+l":
			// Clear chat history
			qv.model.messagePairs = []models.MessagePair{}
			return nil

		case "ctrl+k":
			// Toggle collapse/expand for last message pair
			if len(qv.model.messagePairs) > 0 {
				lastIdx := len(qv.model.messagePairs) - 1
				qv.model.messagePairs[lastIdx].Collapsed = !qv.model.messagePairs[lastIdx].Collapsed
			}
			return nil
		}
	}

	// Update text input
	qv.textInput, cmd = qv.textInput.Update(msg)
	return cmd
}

// View renders the Query view
func (qv *QueryView) View() string {
	var sb strings.Builder

	// Project pane (always visible at top)
	sb.WriteString(qv.renderProjectPane())
	sb.WriteString("\n")

	// Chat window
	sb.WriteString(qv.renderChatWindow())
	sb.WriteString("\n")

	// Input field
	sb.WriteString(qv.renderInput())
	sb.WriteString("\n")

	// Help text
	sb.WriteString(qv.renderHelp())

	return sb.String()
}

// renderProjectPane renders a dedicated pane for the selected project
func (qv *QueryView) renderProjectPane() string {
	if len(qv.model.projects) == 0 {
		return styleBox.Render(styleLoading.Render("Loading projects..."))
	}

	selectedProject := qv.model.projects[qv.model.selectedProject]

	// Single line: Project name followed by description (no newlines)
	projectLine := styleProjectName.Render(selectedProject.Name) + ": " + selectedProject.Description

	// Wrap in a styled box
	return styleBox.Render(projectLine)
}

// renderChatWindow renders the message history
func (qv *QueryView) renderChatWindow() string {
	var sb strings.Builder

	sb.WriteString(styleHeader.Render("Chat"))
	sb.WriteString("\n")

	if len(qv.model.messagePairs) == 0 {
		sb.WriteString(styleHelp.Render("No messages yet. Ask a question below!"))
		return sb.String()
	}

	// Render message pairs
	for _, pair := range qv.model.messagePairs {
		// Always show the query with timestamp prefix
		queryLine := styleTimestamp.Render("("+pair.Query.Timestamp.Format("15:04:05")+")") + " " + styleUserMessage.Render("You: "+pair.Query.Content)
		sb.WriteString(queryLine)

		if pair.Collapsed {
			// Show collapsed indicator for response (same line, one blank line after)
			sb.WriteString(" ")
			sb.WriteString(styleHelp.Render("▸ Response collapsed (press Ctrl+K to expand)"))
			sb.WriteString("\n\n")
		} else {
			// Show response if available
			sb.WriteString("\n")
			if pair.Response.Content != "" {
				sb.WriteString(styleAssistantMessage.Render("Assistant:"))
				sb.WriteString("\n")
				// Word wrap the response
				wrapped := wordWrap(pair.Response.Content, 80)
				sb.WriteString(styleAssistantMessage.Render(wrapped))
				sb.WriteString("\n")
				sb.WriteString(styleTimestamp.Render(pair.Response.Timestamp.Format("15:04:05")))
				sb.WriteString("\n")
			} else {
				sb.WriteString(styleLoading.Render("  ⏳ Thinking..."))
				sb.WriteString("\n")
			}
		}
	}

	return sb.String()
}

// renderInput renders the input field
func (qv *QueryView) renderInput() string {
	var sb strings.Builder

	sb.WriteString(styleInputPrompt.Render("Query: "))
	sb.WriteString(qv.textInput.View())

	if qv.model.loading {
		sb.WriteString(" ")
		sb.WriteString(styleLoading.Render("⏳"))
	}

	return sb.String()
}

// renderHelp renders help text
func (qv *QueryView) renderHelp() string {
	helpItems := []string{
		"enter: submit query",
		"↑/↓: select project",
		"ctrl+k: toggle collapse",
		"ctrl+l: clear chat",
		"tab: switch tab",
		"q/ctrl+c: quit",
	}
	return styleHelp.Render(strings.Join(helpItems, " • "))
}

// submitQuery handles query submission
func (qv *QueryView) submitQuery() tea.Cmd {
	query := strings.TrimSpace(qv.textInput.Value())
	if query == "" {
		return nil
	}

	// Create message pair
	pair := models.MessagePair{
		Query: models.Message{
			Role:      "user",
			Content:   query,
			Timestamp: time.Now(),
		},
		Collapsed: false,
	}

	qv.model.messagePairs = append(qv.model.messagePairs, pair)
	qv.model.loading = true

	// Clear input
	qv.textInput.SetValue("")

	// Get selected project
	projectID := qv.model.projects[qv.model.selectedProject].ID

	// Submit to API
	return qv.model.submitQuery(projectID, query)
}

// wordWrap wraps text to a specified width
func wordWrap(text string, width int) string {
	var result strings.Builder
	lines := strings.Split(text, "\n")

	for _, line := range lines {
		if len(line) <= width {
			result.WriteString(line)
			result.WriteString("\n")
			continue
		}

		words := strings.Fields(line)
		currentLine := ""

		for _, word := range words {
			if len(currentLine)+len(word)+1 <= width {
				if currentLine != "" {
					currentLine += " "
				}
				currentLine += word
			} else {
				if currentLine != "" {
					result.WriteString(currentLine)
					result.WriteString("\n")
				}
				currentLine = word
			}
		}

		if currentLine != "" {
			result.WriteString(currentLine)
			result.WriteString("\n")
		}
	}

	return strings.TrimSuffix(result.String(), "\n")
}
