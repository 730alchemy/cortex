package tui

import (
	"github.com/730alchemy/cortex/apps/cortex-tui/internal/api"
	"github.com/730alchemy/cortex/apps/cortex-tui/internal/config"
	"github.com/730alchemy/cortex/apps/cortex-tui/internal/models"
	tea "github.com/charmbracelet/bubbletea"
)

// TabType represents the different tabs in the TUI
type TabType int

const (
	QueryTab TabType = iota
	ProjectTab
)

// Model is the main application model
type Model struct {
	config *config.Config
	client *api.Client
	logger *Logger

	// Navigation state
	activeTab TabType
	tabs      []string

	// Data
	projects        []models.Project
	selectedProject int
	messagePairs    []models.MessagePair
	currentQuery    string
	infoSources     []models.InformationSource
	sourcesCache    map[string][]models.InformationSource

	// UI state
	width    int
	height   int
	ready    bool
	quitting bool
	err      error
	loading  bool

	// Sub-components
	queryView   *QueryView
	projectView *ProjectView
}

// NewModel creates a new TUI model
func NewModel(cfg *config.Config) *Model {
	client := api.NewClient(cfg.CortexAPI.URL, cfg.CortexAPI.Username, cfg.CortexAPI.Password)

	// Initialize logger
	logger, err := NewLogger(cfg.Logging.Level)
	if err != nil {
		// Fall back to no logging if we can't create the logger
		logger = nil
	} else {
		logger.Info("Cortex TUI started")
	}

	m := &Model{
		config:       cfg,
		client:       client,
		logger:       logger,
		activeTab:    QueryTab,
		tabs:         []string{"Query", "Project"},
		messagePairs: []models.MessagePair{},
		sourcesCache: make(map[string][]models.InformationSource),
	}

	m.queryView = NewQueryView(m)
	m.projectView = NewProjectView(m)

	return m
}

// Init initializes the model
func (m *Model) Init() tea.Cmd {
	return tea.Batch(
		m.loadProjects,
		tea.EnterAltScreen,
	)
}

// Update handles messages and updates the model
func (m *Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmds []tea.Cmd

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		m.ready = true
		// Don't return - let it fall through to delegate to views

	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c":
			m.quitting = true
			return m, tea.Quit

		case "tab":
			// Switch tabs
			if m.activeTab == QueryTab {
				m.activeTab = ProjectTab
			} else {
				m.activeTab = QueryTab
			}
			return m, nil

		case "shift+tab":
			// Switch tabs backwards
			if m.activeTab == ProjectTab {
				m.activeTab = QueryTab
			} else {
				m.activeTab = ProjectTab
			}
			return m, nil
		}

	case projectsLoadedMsg:
		m.projects = msg.projects
		m.loading = false
		if m.logger != nil {
			m.logger.Info("Loaded %d projects", len(m.projects))
		}
		if len(m.projects) > 0 {
			m.selectedProject = 0
			// Load info sources for first project
			return m, m.loadInfoSources(m.projects[0].ID)
		}
		return m, nil

	case infoSourcesLoadedMsg:
		m.infoSources = msg.sources
		// Cache the sources
		if msg.projectID != "" {
			m.sourcesCache[msg.projectID] = msg.sources
		}
		return m, nil

	case queryResponseMsg:
		// Add the response to message pairs
		if len(m.messagePairs) > 0 {
			lastIdx := len(m.messagePairs) - 1
			m.messagePairs[lastIdx].Response = msg.response

			// Trigger viewport update in QueryView after response is added
			if m.activeTab == QueryTab && m.queryView != nil {
				m.queryView.onResponseReceived()
			}
		}
		m.loading = false
		return m, nil

	case errMsg:
		m.err = msg.err
		m.loading = false
		if m.logger != nil {
			m.logger.Error("Error: %v", msg.err)
		}
		return m, nil
	}

	// Delegate to active tab
	switch m.activeTab {
	case QueryTab:
		cmd := m.queryView.Update(msg)
		cmds = append(cmds, cmd)
	case ProjectTab:
		cmd := m.projectView.Update(msg)
		cmds = append(cmds, cmd)
	}

	return m, tea.Batch(cmds...)
}

// View renders the model
func (m *Model) View() string {
	if !m.ready {
		return "Loading..."
	}

	if m.quitting {
		// Clean up logger
		if m.logger != nil {
			m.logger.Info("Cortex TUI shutting down")
			m.logger.Close()
		}
		return "Thanks for using Cortex TUI!\n"
	}

	// Render tabs and active view
	return m.renderTabs() + "\n\n" + m.renderActiveView()
}

// renderTabs renders the tab navigation
func (m *Model) renderTabs() string {
	var tabs string
	for i, tab := range m.tabs {
		if TabType(i) == m.activeTab {
			tabs += styleActiveTab.Render(tab) + " "
		} else {
			tabs += styleInactiveTab.Render(tab) + " "
		}
	}
	return tabs
}

// renderActiveView renders the currently active tab view
func (m *Model) renderActiveView() string {
	switch m.activeTab {
	case QueryTab:
		return m.queryView.View()
	case ProjectTab:
		return m.projectView.View()
	default:
		return "Unknown view"
	}
}

// Commands for async operations

func (m *Model) loadProjects() tea.Msg {
	projects, err := m.client.GetProjects()
	if err != nil {
		return errMsg{err}
	}
	return projectsLoadedMsg{projects}
}

func (m *Model) loadInfoSources(projectID string) tea.Cmd {
	return func() tea.Msg {
		// Check cache first
		if sources, ok := m.sourcesCache[projectID]; ok {
			return infoSourcesLoadedMsg{projectID, sources}
		}

		sources, err := m.client.GetInformationSources(projectID)
		if err != nil {
			return errMsg{err}
		}
		return infoSourcesLoadedMsg{projectID, sources}
	}
}

func (m *Model) submitQuery(projectID, query string) tea.Cmd {
	return func() tea.Msg {
		response, err := m.client.QueryProject(projectID, query)
		if err != nil {
			return errMsg{err}
		}
		return queryResponseMsg{
			response: models.Message{
				Role:      "assistant",
				Content:   response.Response,
				Timestamp: response.Timestamp,
			},
		}
	}
}

// Message types

type projectsLoadedMsg struct {
	projects []models.Project
}

type infoSourcesLoadedMsg struct {
	projectID string
	sources   []models.InformationSource
}

type queryResponseMsg struct {
	response models.Message
}

type errMsg struct {
	err error
}
