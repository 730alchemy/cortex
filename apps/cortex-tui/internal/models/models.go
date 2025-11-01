package models

import "time"

// Project represents a software project in Cortex
type Project struct {
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	Description string    `json:"description"`
	CreatedAt   time.Time `json:"created_at"`
}

// Message represents a chat message (query or response)
type Message struct {
	ID        string    `json:"id"`
	Role      string    `json:"role"` // "user" or "assistant"
	Content   string    `json:"content"`
	Timestamp time.Time `json:"timestamp"`
	Collapsed bool      `json:"-"` // UI state only
}

// MessagePair represents a query-response pair
type MessagePair struct {
	Query     Message
	Response  Message
	Collapsed bool // If true, both query and response are collapsed
}

// InformationSource represents a data source for a project
type InformationSource struct {
	Name       string                 `json:"name"`
	Type       string                 `json:"type"` // github, notion, linear, googledocs, etc.
	Attributes map[string]interface{} `json:"attributes"`
}

// QueryRequest represents a request to query the Cortex API
type QueryRequest struct {
	ProjectID string `json:"project_id"`
	Query     string `json:"query"`
}

// QueryResponse represents the response from a Cortex query
type QueryResponse struct {
	Response  string    `json:"response"`
	Timestamp time.Time `json:"timestamp"`
}
