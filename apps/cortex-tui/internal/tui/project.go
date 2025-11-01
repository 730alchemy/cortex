package tui

import (
	"fmt"
	"strings"

	"github.com/730alchemy/cortex/apps/cortex-tui/internal/models"
	tea "github.com/charmbracelet/bubbletea"
)

// ProjectView represents the Project tab
type ProjectView struct {
	model *Model
}

// NewProjectView creates a new Project view
func NewProjectView(m *Model) *ProjectView {
	return &ProjectView{
		model: m,
	}
}

// Update handles updates for the Project view
func (pv *ProjectView) Update(msg tea.Msg) tea.Cmd {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "up":
			// Navigate project selector
			if pv.model.selectedProject > 0 {
				pv.model.selectedProject--
				projectID := pv.model.projects[pv.model.selectedProject].ID
				return pv.model.loadInfoSources(projectID)
			}
			return nil

		case "down":
			// Navigate project selector
			if pv.model.selectedProject < len(pv.model.projects)-1 {
				pv.model.selectedProject++
				projectID := pv.model.projects[pv.model.selectedProject].ID
				return pv.model.loadInfoSources(projectID)
			}
			return nil

		case "r":
			// Refresh information sources
			if pv.model.selectedProject < len(pv.model.projects) {
				projectID := pv.model.projects[pv.model.selectedProject].ID
				// Remove from cache to force refresh
				delete(pv.model.sourcesCache, projectID)
				return pv.model.loadInfoSources(projectID)
			}
			return nil
		}
	}

	return nil
}

// View renders the Project view
func (pv *ProjectView) View() string {
	var sb strings.Builder

	// Project info
	sb.WriteString(pv.renderProjectInfo())
	sb.WriteString("\n\n")

	// Information sources
	sb.WriteString(pv.renderInformationSources())
	sb.WriteString("\n")

	// Help text
	sb.WriteString(pv.renderHelp())

	return sb.String()
}

// renderProjectInfo renders the selected project information
func (pv *ProjectView) renderProjectInfo() string {
	var sb strings.Builder

	sb.WriteString(styleHeader.Render("Project Information"))
	sb.WriteString("\n\n")

	if len(pv.model.projects) == 0 {
		sb.WriteString(styleLoading.Render("Loading projects..."))
		return sb.String()
	}

	selectedProject := pv.model.projects[pv.model.selectedProject]

	// Project name
	sb.WriteString(styleSubHeader.Render(selectedProject.Name))
	sb.WriteString("\n")

	// Description
	sb.WriteString(styleSourceAttr.Render("Description: "))
	sb.WriteString(selectedProject.Description)
	sb.WriteString("\n\n")

	// ID
	sb.WriteString(styleSourceAttr.Render("ID: "))
	sb.WriteString(selectedProject.ID)
	sb.WriteString("\n")

	// Created date
	sb.WriteString(styleSourceAttr.Render("Created: "))
	sb.WriteString(selectedProject.CreatedAt.Format("2006-01-02"))
	sb.WriteString("\n\n")

	// Navigation hint
	sb.WriteString(styleHelp.Render(fmt.Sprintf("↑/↓ to switch projects (%d/%d)",
		pv.model.selectedProject+1, len(pv.model.projects))))

	return sb.String()
}

// renderInformationSources renders the information sources for the project
func (pv *ProjectView) renderInformationSources() string {
	var sb strings.Builder

	sb.WriteString(styleHeader.Render("Information Sources"))
	sb.WriteString("\n\n")

	if len(pv.model.infoSources) == 0 {
		sb.WriteString(styleHelp.Render("No information sources configured for this project"))
		return sb.String()
	}

	// Render each source
	for i, source := range pv.model.infoSources {
		sb.WriteString(pv.renderSource(source, i+1))
		if i < len(pv.model.infoSources)-1 {
			sb.WriteString("\n")
		}
	}

	return sb.String()
}

// renderSource renders a single information source
func (pv *ProjectView) renderSource(source models.InformationSource, index int) string {
	var sb strings.Builder

	// Source number and name
	sb.WriteString(styleSourceName.Render(fmt.Sprintf("%d. %s", index, source.Name)))
	sb.WriteString("\n")

	// Type with icon
	typeIcon := getSourceTypeIcon(source.Type)
	sb.WriteString("   ")
	sb.WriteString(styleSourceType.Render(fmt.Sprintf("%s %s", typeIcon, source.Type)))
	sb.WriteString("\n")

	// Render type-specific attributes
	sb.WriteString(pv.renderSourceAttributes(source.Type, source.Attributes))

	return sb.String()
}

// renderSourceAttributes renders attributes based on source type
func (pv *ProjectView) renderSourceAttributes(sourceType string, attrs map[string]interface{}) string {
	var sb strings.Builder

	switch sourceType {
	case "github":
		if repo, ok := attrs["repo"].(string); ok {
			sb.WriteString("   ")
			sb.WriteString(styleSourceAttr.Render("Repository: "))
			sb.WriteString(repo)
			sb.WriteString("\n")
		}
		if url, ok := attrs["url"].(string); ok {
			sb.WriteString("   ")
			sb.WriteString(styleSourceAttr.Render("URL: "))
			sb.WriteString(url)
			sb.WriteString("\n")
		}

	case "notion":
		if workspace, ok := attrs["workspace"].(string); ok {
			sb.WriteString("   ")
			sb.WriteString(styleSourceAttr.Render("Workspace: "))
			sb.WriteString(workspace)
			sb.WriteString("\n")
		}
		if wsID, ok := attrs["workspace_id"].(string); ok {
			sb.WriteString("   ")
			sb.WriteString(styleSourceAttr.Render("Workspace ID: "))
			sb.WriteString(wsID)
			sb.WriteString("\n")
		}

	case "linear":
		if team, ok := attrs["team"].(string); ok {
			sb.WriteString("   ")
			sb.WriteString(styleSourceAttr.Render("Team: "))
			sb.WriteString(team)
			sb.WriteString("\n")
		}
		if project, ok := attrs["project"].(string); ok {
			sb.WriteString("   ")
			sb.WriteString(styleSourceAttr.Render("Project: "))
			sb.WriteString(project)
			sb.WriteString("\n")
		}

	case "googledocs":
		if folder, ok := attrs["folder"].(string); ok {
			sb.WriteString("   ")
			sb.WriteString(styleSourceAttr.Render("Folder: "))
			sb.WriteString(folder)
			sb.WriteString("\n")
		}
		if docID, ok := attrs["doc_id"].(string); ok {
			sb.WriteString("   ")
			sb.WriteString(styleSourceAttr.Render("Document ID: "))
			sb.WriteString(docID)
			sb.WriteString("\n")
		}

	default:
		// Generic attribute rendering
		for key, value := range attrs {
			sb.WriteString("   ")
			sb.WriteString(styleSourceAttr.Render(fmt.Sprintf("%s: %v", key, value)))
			sb.WriteString("\n")
		}
	}

	return sb.String()
}

// getSourceTypeIcon returns an icon for a source type
func getSourceTypeIcon(sourceType string) string {
	icons := map[string]string{
		"github":     "🐙",
		"notion":     "📝",
		"linear":     "📊",
		"googledocs": "📄",
		"gitlab":     "🦊",
		"jira":       "🎫",
		"confluence": "🌐",
	}

	if icon, ok := icons[sourceType]; ok {
		return icon
	}
	return "📦"
}

// renderHelp renders help text
func (pv *ProjectView) renderHelp() string {
	helpItems := []string{
		"↑/↓: select project",
		"r: refresh sources",
		"tab: switch tab",
		"q/ctrl+c: quit",
	}
	return styleHelp.Render(strings.Join(helpItems, " • "))
}
