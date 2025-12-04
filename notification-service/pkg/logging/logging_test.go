package logging

import (
	"errors"
	"testing"

	"go.uber.org/zap/zapcore"
)

func TestLogger(t *testing.T) {
	productionLogger, err := NewLogger(Config{
		ServiceName: "test",
		Version:     "1.0.0",
		Environment: "production",
		LogLevel:    zapcore.InfoLevel,
	})

	if err != nil {
		t.Fatal(err)
	}

	productionLogger.Info("test")
	productionLogger.Debug("test") // This won't print since the log level in production is info
	productionLogger.Error("test", errors.New("test"))

	devLogger, err := NewLogger(Config{
		ServiceName: "test",
		Version:     "1.0.0",
		Environment: "dev",
		LogLevel:    zapcore.DebugLevel,
	})

	if err != nil {
		t.Fatal(err)
	}

	devLogger.Info("test")
	devLogger.Debug("test") // This will print since the log level in dev is debug
	devLogger.Error("test", errors.New("test"))
}
