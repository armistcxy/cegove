.PHONY: help generate run build test clean install-tools fmt lint deps

# Default target
help:
	@echo "Notification Service - Available Commands"
	@echo "=========================================="
	@echo "make generate    - Generate proto code from proto files"
	@echo "make build       - Build the notification service binary"
	@echo "make run         - Run the notification service"
	@echo "make test        - Run unit tests"
	@echo "make clean       - Clean generated code and build artifacts"
	@echo "make install-tools - Install required tools (protoc plugins)"
	@echo "make fmt         - Format Go code"
	@echo "make lint        - Run go linter"
	@echo "make deps        - Download and tidy dependencies"

# Generate Go and gRPC code from proto files
generate:
	@echo "Generating Go and gRPC code from proto files..."
	@bash gen-proto.sh
	@echo "✓ Code generation complete"

# Build the notification service binary
build: generate
	@echo "Building notification service..."
	@go build -o bin/notification-service ./cmd
	@echo "✓ Build complete: bin/notification-service"

# Run the notification service
run: generate
	@echo "Starting notification service..."
	@go run ./cmd

# Run tests
test:
	@echo "Running tests..."
	@go test -v ./...

# Clean generated code and build artifacts
clean:
	@echo "Cleaning generated code and build artifacts..."
	@rm -rf api/
	@rm -rf docs/
	@rm -rf bin/
	@go clean
	@echo "✓ Clean complete"

# Install required tools
install-tools:
	@echo "Installing protoc tools..."
	@go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
	@go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
	@go install github.com/grpc-ecosystem/grpc-gateway/v2/protoc-gen-grpc-gateway@latest
	@go install github.com/grpc-ecosystem/grpc-gateway/v2/protoc-gen-openapiv2@latest
	@echo "✓ Tools installed"

# Format Go code
fmt:
	@echo "Formatting Go code..."
	@go fmt ./...
	@echo "✓ Format complete"

# Lint code
lint:
	@echo "Running linter..."
	@golangci-lint run ./...
	@echo "✓ Lint complete"

# Download and tidy dependencies
deps:
	@echo "Downloading and tidying dependencies..."
	@go mod download
	@go mod tidy
	@echo "✓ Dependencies updated"

# Run linter
lint:
	@echo "Running linter..."
	@golangci-lint run ./...
	@echo "✓ Lint complete"

# Generate, build, and run (development)
dev: generate run

# Dependencies
deps:
	@echo "Downloading dependencies..."
	@go mod download
	@go mod tidy
	@echo "✓ Dependencies downloaded"
