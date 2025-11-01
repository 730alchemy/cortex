package api

import (
	"fmt"
	"time"

	"github.com/730alchemy/cortex/apps/cortex-tui/internal/models"
)

// Client represents a Cortex API client
type Client struct {
	baseURL  string
	username string
	password string
}

// NewClient creates a new API client
func NewClient(baseURL, username, password string) *Client {
	return &Client{
		baseURL:  baseURL,
		username: username,
		password: password,
	}
}

// GetProjects returns all projects available to the user (STUBBED with dummy data)
func (c *Client) GetProjects() ([]models.Project, error) {
	// Return dummy projects
	return []models.Project{
		{
			ID:          "proj-1",
			Name:        "Cortex Knowledge System",
			Description: "AI-powered knowledge management for software projects",
			CreatedAt:   time.Now().Add(-30 * 24 * time.Hour),
		},
		{
			ID:          "proj-2",
			Name:        "E-Commerce Platform",
			Description: "Microservices-based online shopping platform",
			CreatedAt:   time.Now().Add(-60 * 24 * time.Hour),
		},
		{
			ID:          "proj-3",
			Name:        "Mobile Banking App",
			Description: "iOS and Android banking application",
			CreatedAt:   time.Now().Add(-90 * 24 * time.Hour),
		},
	}, nil
}

// QueryProject sends a query to the Cortex API for a specific project (STUBBED with dummy data)
func (c *Client) QueryProject(projectID, query string) (*models.QueryResponse, error) {
	// Simulate some processing delay
	time.Sleep(500 * time.Millisecond)

	// Return dummy response based on query keywords
	response := generateDummyResponse(query)

	return &models.QueryResponse{
		Response:  response,
		Timestamp: time.Now(),
	}, nil
}

// GetInformationSources returns information sources for a project (STUBBED with dummy data)
func (c *Client) GetInformationSources(projectID string) ([]models.InformationSource, error) {
	// Return dummy sources based on project
	switch projectID {
	case "proj-1":
		return []models.InformationSource{
			{
				Name: "cortex-main",
				Type: "github",
				Attributes: map[string]interface{}{
					"repo": "730alchemy/cortex",
					"url":  "https://github.com/730alchemy/cortex",
				},
			},
			{
				Name: "Project Documentation",
				Type: "notion",
				Attributes: map[string]interface{}{
					"workspace":    "Cortex Team",
					"workspace_id": "ws-12345",
				},
			},
			{
				Name: "Feature Tracker",
				Type: "linear",
				Attributes: map[string]interface{}{
					"team":    "Engineering",
					"project": "Cortex",
				},
			},
		}, nil
	case "proj-2":
		return []models.InformationSource{
			{
				Name: "ecommerce-backend",
				Type: "github",
				Attributes: map[string]interface{}{
					"repo": "company/ecommerce-api",
					"url":  "https://github.com/company/ecommerce-api",
				},
			},
			{
				Name: "Architecture Docs",
				Type: "googledocs",
				Attributes: map[string]interface{}{
					"folder": "E-Commerce Architecture",
					"doc_id": "doc-67890",
				},
			},
		}, nil
	case "proj-3":
		return []models.InformationSource{
			{
				Name: "banking-ios",
				Type: "github",
				Attributes: map[string]interface{}{
					"repo": "fintech/banking-ios",
					"url":  "https://github.com/fintech/banking-ios",
				},
			},
			{
				Name: "banking-android",
				Type: "github",
				Attributes: map[string]interface{}{
					"repo": "fintech/banking-android",
					"url":  "https://github.com/fintech/banking-android",
				},
			},
			{
				Name: "Product Requirements",
				Type: "notion",
				Attributes: map[string]interface{}{
					"workspace":    "Product Team",
					"workspace_id": "ws-54321",
				},
			},
		}, nil
	default:
		return []models.InformationSource{}, nil
	}
}

// generateDummyResponse creates a contextual dummy response based on query
func generateDummyResponse(query string) string {
	responses := map[string]string{
		"architecture":   "The system follows a microservices architecture with the following components:\n\n1. API Gateway: Handles routing and authentication\n2. Service Layer: Domain-specific services (auth, products, orders)\n3. Data Layer: PostgreSQL for transactional data, Redis for caching\n4. Message Queue: RabbitMQ for async processing\n\nAll services communicate via REST APIs and publish events to the message queue for cross-service coordination.",
		"authentication": "Authentication is handled using JWT tokens with the following flow:\n\n1. User submits credentials to /auth/login\n2. Backend validates against user database\n3. On success, generates JWT with 1-hour expiration\n4. Frontend stores token and includes in Authorization header\n5. API Gateway validates token on each request\n6. Refresh tokens are used for extended sessions\n\nThe system also supports OAuth2 for third-party authentication via Google and GitHub.",
		"database":       "The database schema consists of several key tables:\n\n- users: User accounts and profiles\n- projects: Project metadata and ownership\n- documents: Indexed documents and their embeddings\n- queries: Query history and analytics\n- sources: Information source configurations\n\nAll tables use UUID primary keys and include created_at/updated_at timestamps. Indexes are optimized for common query patterns.",
		"testing":        "The testing strategy includes:\n\n1. Unit Tests: Jest/Go testing for business logic (80%+ coverage)\n2. Integration Tests: API endpoint testing with test database\n3. E2E Tests: Playwright for critical user flows\n4. Load Tests: k6 for performance validation\n\nCI/CD pipeline runs all tests on PRs. E2E tests run on staging deployments.",
	}

	// Match keywords to responses
	for keyword, response := range responses {
		if contains(query, keyword) {
			return response
		}
	}

	// Default response
	return fmt.Sprintf("Based on my analysis of the codebase, here's what I found regarding your query:\n\n\"%s\"\n\nThe system implements this feature across multiple modules with proper separation of concerns. The main implementation can be found in the service layer, with supporting infrastructure in the data access layer.\n\nKey components:\n- Service orchestration in the application layer\n- Data persistence via repository pattern\n- Event-driven updates for real-time synchronization\n- Caching for performance optimization\n\nWould you like more specific details about any particular aspect?", query)
}

// contains checks if a string contains a substring (case-insensitive)
func contains(s, substr string) bool {
	s = toLower(s)
	substr = toLower(substr)
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}

// toLower converts string to lowercase
func toLower(s string) string {
	result := make([]rune, len(s))
	for i, r := range s {
		if r >= 'A' && r <= 'Z' {
			result[i] = r + 32
		} else {
			result[i] = r
		}
	}
	return string(result)
}
