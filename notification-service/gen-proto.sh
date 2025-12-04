#!/usr/bin/env bash
set -e

ROOT_DIR="$(git rev-parse --show-toplevel)/notification-service"
PROTO_DIR="$ROOT_DIR/proto"
OUT_DIR="$ROOT_DIR/api"
SWAGGER_DIR="$ROOT_DIR/docs"

echo "Generating Go and Swagger code from proto files..."

# Clean old generated code
rm -rf "$OUT_DIR"
rm -rf "$SWAGGER_DIR"
mkdir -p "$OUT_DIR"
mkdir -p "$SWAGGER_DIR"

# Find all proto files
PROTO_FILES=$(find "$PROTO_DIR" -name "*.proto")
if [ -z "$PROTO_FILES" ]; then
  echo "No .proto files found."
  exit 0
fi

echo "→ Processing all proto files..."
protoc \
    -I="$PROTO_DIR" \
    --go_out="$OUT_DIR" \
    --go_opt=paths=source_relative \
    --go-grpc_out="$OUT_DIR" \
    --go-grpc_opt=paths=source_relative \
    --grpc-gateway_out="$OUT_DIR" \
    --grpc-gateway_opt=paths=source_relative \
    --openapiv2_out="$SWAGGER_DIR" \
    --openapiv2_opt logtostderr=true \
    $PROTO_FILES

echo "Done."