package tui

import (
	"strings"
	"time"

	"github.com/730alchemy/cortex/apps/cortex-tui/internal/models"
	"github.com/charmbracelet/bubbles/textinput"
	"github.com/charmbracelet/bubbles/viewport"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// QueryView represents the Query tab
type QueryView struct {
	model        *Model
	textInput    textinput.Model
	chatViewport viewport.Model
	cursorIdx    int  // Current message index in non-follow mode
	follow       bool // Auto-scroll to newest messages
	ready        bool
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
		cursorIdx: -1,
		follow:    true, // Start in follow mode
		ready:     false,
	}
}

// Update handles updates for the Query view
func (qv *QueryView) Update(msg tea.Msg) tea.Cmd {
	var cmd tea.Cmd

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		// Initialize or resize viewport
		if !qv.ready {
			// Calculate heights
			projectPaneHeight := lipgloss.Height(qv.renderProjectPane())
			chatHeaderHeight := 2 // "Chat\n"
			inputHeight := lipgloss.Height(qv.renderInput())
			helpHeight := lipgloss.Height(qv.renderHelp())

			viewportHeight := msg.Height - projectPaneHeight - chatHeaderHeight - inputHeight - helpHeight - 2
			if viewportHeight < 5 {
				viewportHeight = 5
			}

			qv.chatViewport = viewport.New(msg.Width, viewportHeight)
			qv.chatViewport.YPosition = projectPaneHeight + chatHeaderHeight
			qv.ready = true

			// Set initial content
			qv.updateViewportContent()
		} else {
			// Resize existing viewport
			projectPaneHeight := lipgloss.Height(qv.renderProjectPane())
			chatHeaderHeight := 2
			inputHeight := lipgloss.Height(qv.renderInput())
			helpHeight := lipgloss.Height(qv.renderHelp())

			viewportHeight := msg.Height - projectPaneHeight - chatHeaderHeight - inputHeight - helpHeight - 2
			if viewportHeight < 5 {
				viewportHeight = 5
			}

			qv.chatViewport.Width = msg.Width
			qv.chatViewport.Height = viewportHeight

			// Rewrap all messages with new width
			qv.rewrapAll(msg.Width)

			// Restore scroll position
			if qv.follow {
				qv.chatViewport.GotoBottom()
			} else if qv.cursorIdx >= 0 {
				qv.scrollToMessagePair(qv.cursorIdx)
			}
		}

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

		case "ctrl+up":
			// Navigate to previous message
			if len(qv.model.messagePairs) > 0 {
				if qv.cursorIdx == -1 || qv.cursorIdx >= len(qv.model.messagePairs) {
					qv.cursorIdx = len(qv.model.messagePairs) - 1
				} else if qv.cursorIdx > 0 {
					qv.cursorIdx--
				}
				qv.follow = false
				qv.updateViewportContent()
				qv.scrollToMessagePair(qv.cursorIdx)
			}
			return nil

		case "ctrl+down":
			// Navigate to next message
			if len(qv.model.messagePairs) > 0 {
				if qv.cursorIdx == -1 || qv.cursorIdx >= len(qv.model.messagePairs) {
					qv.cursorIdx = len(qv.model.messagePairs) - 1
				} else if qv.cursorIdx < len(qv.model.messagePairs)-1 {
					qv.cursorIdx++
					qv.scrollToMessagePair(qv.cursorIdx)
				} else {
					// At last message, enable follow mode
					qv.follow = true
					qv.chatViewport.GotoBottom()
				}
				qv.updateViewportContent()
			}
			return nil

		case "ctrl+l":
			// Clear chat history
			qv.model.messagePairs = []models.MessagePair{}
			qv.cursorIdx = -1
			qv.follow = true
			qv.updateViewportContent()
			return nil

		case "ctrl+k":
			// Toggle collapse/expand for selected message pair
			if len(qv.model.messagePairs) > 0 {
				idx := qv.cursorIdx
				if idx == -1 {
					idx = len(qv.model.messagePairs) - 1
				}
				qv.model.messagePairs[idx].Collapsed = !qv.model.messagePairs[idx].Collapsed

				// Rewrap since collapsed state affects line count
				qv.rewrapAll(qv.chatViewport.Width)
				qv.updateViewportContent()

				if !qv.follow {
					qv.scrollToMessagePair(qv.cursorIdx)
				}
			}
			return nil

		case "ctrl+a":
			// Toggle collapse/expand for all message pairs
			if len(qv.model.messagePairs) > 0 {
				// Determine target state: if any message is expanded, collapse all; otherwise expand all
				allCollapsed := true
				for _, pair := range qv.model.messagePairs {
					if !pair.Collapsed {
						allCollapsed = false
						break
					}
				}

				// Toggle all messages to opposite state
				targetState := !allCollapsed
				for i := range qv.model.messagePairs {
					qv.model.messagePairs[i].Collapsed = targetState
				}

				// Rewrap since collapsed state affects line count
				qv.rewrapAll(qv.chatViewport.Width)
				qv.updateViewportContent()

				if !qv.follow && qv.cursorIdx >= 0 {
					qv.scrollToMessagePair(qv.cursorIdx)
				}
			}
			return nil
		}
	}

	// Update text input
	qv.textInput, cmd = qv.textInput.Update(msg)

	// Pass messages to viewport for mouse wheel support
	if qv.ready {
		qv.chatViewport, _ = qv.chatViewport.Update(msg)
	}

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

// renderChatContent renders just the chat messages (without header)
func (qv *QueryView) renderChatContent() string {
	if len(qv.model.messagePairs) == 0 {
		return styleHelp.Render("No messages yet. Ask a question below!")
	}

	var sb strings.Builder

	// Render message pairs
	for i, pair := range qv.model.messagePairs {
		// Determine if this message is selected (only show indicator in non-follow mode)
		isSelected := !qv.follow && qv.cursorIdx == i

		// Add selection indicator if selected
		selectionIndicator := ""
		if isSelected {
			selectionIndicator = styleSelectedItem.Render("▸ ")
		} else {
			selectionIndicator = "  " // Two spaces for alignment
		}

		// Always show the query with timestamp prefix and selection indicator
		queryLine := selectionIndicator + styleTimestamp.Render("("+pair.Query.Timestamp.Format("15:04:05")+")") + " " + styleUserMessage.Render("You: "+pair.Query.Content)
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

				// Use pre-wrapped text if available, otherwise wrap now
				var wrapped string
				if len(pair.Response.Wrapped) > 0 {
					wrapped = strings.Join(pair.Response.Wrapped, "\n")
				} else {
					wrapped = wordWrap(pair.Response.Content, 80)
				}

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

// renderChatWindow renders the message history with header and viewport
func (qv *QueryView) renderChatWindow() string {
	if !qv.ready {
		return styleHeader.Render("Chat") + "\n" + "Initializing..."
	}

	var sb strings.Builder
	sb.WriteString(styleHeader.Render("Chat"))
	sb.WriteString("\n")
	sb.WriteString(qv.chatViewport.View())

	return sb.String()
}

// updateViewportContent updates the viewport content (call in Update, not View)
func (qv *QueryView) updateViewportContent() {
	if qv.ready {
		content := qv.renderChatContent()
		qv.chatViewport.SetContent(content)
	}
}

// offsetOf calculates the exact row offset for a message pair
func (qv *QueryView) offsetOf(pairIdx int) int {
	if pairIdx < 0 || pairIdx >= len(qv.model.messagePairs) {
		return 0
	}

	offset := 0
	for i := 0; i < pairIdx; i++ {
		pair := qv.model.messagePairs[i]

		// Query line (always 1 line)
		offset += 1

		if pair.Collapsed {
			// Collapsed: 1 blank line
			offset += 1
		} else {
			// Response section
			if pair.Response.Content != "" {
				// "Assistant:" header
				offset += 1

				// Wrapped response lines
				if len(pair.Response.Wrapped) > 0 {
					offset += len(pair.Response.Wrapped)
				} else {
					// Fallback: estimate based on content
					wrapped := wordWrap(pair.Response.Content, 80)
					offset += len(strings.Split(wrapped, "\n"))
				}

				// Timestamp line
				offset += 1
			} else {
				// "Thinking..." line
				offset += 1
			}
		}
	}

	return offset
}

// scrollToMessagePair scrolls viewport to show the selected message pair
func (qv *QueryView) scrollToMessagePair(idx int) {
	if !qv.ready || idx < 0 || idx >= len(qv.model.messagePairs) {
		return
	}

	targetOffset := qv.offsetOf(idx)
	qv.chatViewport.SetYOffset(targetOffset)
}

// rewrapAll re-wraps all message content when terminal width changes
func (qv *QueryView) rewrapAll(width int) {
	wrapWidth := 80
	if width > 0 && width < 100 {
		wrapWidth = width - 20 // Leave some margin
	}

	for i := range qv.model.messagePairs {
		// Wrap query
		if qv.model.messagePairs[i].Query.Content != "" {
			qv.model.messagePairs[i].Query.Wrapped = wrapLines(qv.model.messagePairs[i].Query.Content, wrapWidth)
		}

		// Wrap response
		if qv.model.messagePairs[i].Response.Content != "" {
			qv.model.messagePairs[i].Response.Wrapped = wrapLines(qv.model.messagePairs[i].Response.Content, wrapWidth)
		}
	}

	// Update viewport content after rewrapping
	qv.updateViewportContent()
}

// wrapLines wraps text and returns as a slice of lines
func wrapLines(text string, width int) []string {
	if text == "" {
		return []string{}
	}

	var result []string
	lines := strings.Split(text, "\n")

	for _, line := range lines {
		if len(line) <= width {
			result = append(result, line)
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
					result = append(result, currentLine)
				}
				currentLine = word
			}
		}

		if currentLine != "" {
			result = append(result, currentLine)
		}
	}

	return result
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
		"ctrl+↑/↓: navigate messages",
		"ctrl+k: toggle collapse",
		"ctrl+a: toggle collapse all",
		"ctrl+l: clear chat",
		"tab: switch tab",
		"ctrl+c: quit",
	}
	return styleHelp.Render(strings.Join(helpItems, " • "))
}

// submitQuery handles query submission
func (qv *QueryView) submitQuery() tea.Cmd {
	query := strings.TrimSpace(qv.textInput.Value())
	if query == "" {
		return nil
	}

	// Determine wrap width
	wrapWidth := 80
	if qv.ready && qv.chatViewport.Width > 0 && qv.chatViewport.Width < 100 {
		wrapWidth = qv.chatViewport.Width - 20
	}

	// Create message pair with wrapped content
	queryMsg := models.Message{
		Role:      "user",
		Content:   query,
		Timestamp: time.Now(),
		Wrapped:   wrapLines(query, wrapWidth),
	}

	pair := models.MessagePair{
		Query:     queryMsg,
		Collapsed: false,
	}

	qv.model.messagePairs = append(qv.model.messagePairs, pair)
	qv.model.loading = true

	// Update viewport content
	qv.updateViewportContent()

	// Always re-enable follow mode and scroll to bottom when submitting new query
	qv.follow = true
	qv.cursorIdx = len(qv.model.messagePairs) - 1
	if qv.ready {
		qv.chatViewport.GotoBottom()
	}

	// Clear input
	qv.textInput.SetValue("")

	// Get selected project
	projectID := qv.model.projects[qv.model.selectedProject].ID

	// Submit to API
	return qv.model.submitQuery(projectID, query)
}

// wordWrap wraps text to a specified width (legacy function for compatibility)
func wordWrap(text string, width int) string {
	lines := wrapLines(text, width)
	return strings.Join(lines, "\n")
}

// onResponseReceived is called when a response is received from the API
func (qv *QueryView) onResponseReceived() {
	if !qv.ready || len(qv.model.messagePairs) == 0 {
		return
	}

	// Wrap the response content
	lastIdx := len(qv.model.messagePairs) - 1
	if qv.model.messagePairs[lastIdx].Response.Content != "" {
		wrapWidth := 80
		if qv.chatViewport.Width > 0 && qv.chatViewport.Width < 100 {
			wrapWidth = qv.chatViewport.Width - 20
		}

		qv.model.messagePairs[lastIdx].Response.Wrapped = wrapLines(
			qv.model.messagePairs[lastIdx].Response.Content,
			wrapWidth,
		)
	}

	// Update viewport content
	qv.updateViewportContent()

	// If in follow mode, scroll to bottom
	if qv.follow {
		qv.chatViewport.GotoBottom()
	}
}
