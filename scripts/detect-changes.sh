#!/bin/bash
if [ "$GITHUB_EVENT_NAME" == "pull_request" ]; then
  CHANGED_FILES=$(git diff --name-only origin/$GITHUB_BASE_REF...)
else
  CHANGED_FILES=$(git diff --name-only $GITHUB_EVENT_BEFORE..$GITHUB_SHA)
fi

echo "Changed files:"
echo "$CHANGED_FILES"

SERVICES=(
  "admin-service"
  "booking-service"
  "book-service"
  "cinema-service"
  "frontend"
  "movie-service"
  "notification-service"
  "payment-service"
  "recommendation-service"
  "user-service"
)

# Detect services has changed
CHANGED_SERVICES=()

for service in "${SERVICES[@]}"; do
    if echo "$CHANGED_FILES" | grep -q "^${service}/"; then
        CHANGED_SERVICES+=("$service")
    fi

if echo "$CHANGED_FILES" | grep -q "^scripts/\|^.github/"; then
  echo "Shared files changed, building all services"
  CHANGED_SERVICES=("${SERVICES[@]}")
fi

# Output JSON array for Github Actions matrix
if [ ${#CHANGED_SERVICES[@]} -eq 0 ]; then
  echo "services=[]" >> $GITHUB_OUTPUT
else
  SERVICES_JSON=$(printf '%s\n' "${CHANGED_SERVICES[@]}" | jq -R . | jq -s -c .)
  echo "services=$SERVICES_JSON" >> $GITHUB_OUTPUT
fi

echo "Changed services: ${CHANGED_SERVICES[@]}"