# ---- Build stage ----
FROM golang:1.24-alpine AS builder 


WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

ARG BIN_PATH=./cmd/main.go

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o application ${BIN_PATH}

# ---- Run stage ----
FROM alpine:3.20
WORKDIR /root/

COPY --from=builder /app/application .

CMD ["./application"]