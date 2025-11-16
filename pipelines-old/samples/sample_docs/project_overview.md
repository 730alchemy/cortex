# Cortex Project Overview

## Introduction

Cortex is an AI-powered knowledge management system that transforms how teams interact with their project information.

## Key Features

### Conversational Interface
- Ask questions in natural language
- Get AI-generated answers from your knowledge base
- Context-aware responses that cite sources

### Knowledge Graph
- Entities and relationships automatically extracted
- Navigate between related concepts
- Discover gaps and conflicts in documentation

### Multi-Source Integration
- Connect to GitHub, Notion, Confluence, Google Docs
- Unified search across all sources
- Single source of truth for project knowledge

## Architecture

The system consists of:
1. **Data Pipeline**: Ingests and processes documents
2. **Knowledge Graph**: Stores entities and relationships in Neo4j
3. **Vector Store**: Enables semantic search with embeddings
4. **API Gateway**: Provides unified access to all components
5. **TUI Client**: Terminal-based interface for queries

## Technology Stack

- **Backend**: TypeScript/Node.js, Python
- **Graph DB**: Neo4j
- **Vector DB**: Qdrant
- **Pipeline**: Dagster, DuckDB, Apache Iceberg
- **TUI**: Go with Bubble Tea framework

## Getting Started

See the main README for installation and setup instructions.
