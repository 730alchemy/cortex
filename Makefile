.PHONY: help build clean test lint fmt bootstrap cortex-tui

help: ## Show this help message
	@echo "Cortex Monorepo - Available targets:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

bootstrap: ## Install toolchains and set up workspaces
	@echo "Setting up Cortex development environment..."
	@which go > /dev/null || (echo "Go not installed. Please install Go 1.21+" && exit 1)
	@echo "Go: $(shell go version)"
	@echo "Bootstrap complete"

build: cortex-tui ## Build all projects

clean: ## Clean all build artifacts
	@echo "Cleaning all projects..."
	@cd apps/cortex-tui && $(MAKE) clean
	@echo "Clean complete"

test: ## Run all tests
	@echo "Running all tests..."
	@cd apps/cortex-tui && $(MAKE) test
	@echo "Tests complete"

lint: ## Run linters on all projects
	@echo "Linting all projects..."
	@cd apps/cortex-tui && $(MAKE) lint
	@echo "Lint complete"

fmt: ## Format all code
	@echo "Formatting all projects..."
	@cd apps/cortex-tui && $(MAKE) fmt
	@echo "Format complete"

cortex-tui: ## Build cortex-tui application
	@echo "Building cortex-tui..."
	@cd apps/cortex-tui && $(MAKE) build
	@echo "Built apps/cortex-tui/bin/cortex-tui"

run-tui: cortex-tui ## Build and run cortex-tui
	@cd apps/cortex-tui && $(MAKE) run
