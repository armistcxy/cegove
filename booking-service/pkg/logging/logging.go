package logging

import (
	"context"
	"time"

	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

type Logger struct {
	l *zap.Logger
}

type ctxKey struct{}

var defaultLogger *Logger

func init() {
	l, _ := zap.NewProduction(zap.WithCaller(false))
	defaultLogger = &Logger{
		l: l,
	}
}

// Config is the configuration for the logger
type Config struct {
	ServiceName string
	Version     string

	// Environment is the environment the service is running in.
	//
	// If the Environment is "dev" or "local", the logger will output in human-readable format.
	Environment string

	LogLevel zapcore.Level
}

// NewLogger creates a new logger instance
func NewLogger(cfg Config) (*Logger, error) {
	var zapCfg zap.Config
	if cfg.Environment == "dev" || cfg.Environment == "local" {
		zapCfg = zap.NewDevelopmentConfig()

		// Default log level for dev is debug
		cfg.LogLevel = zapcore.DebugLevel

		// Add color to the log level
		zapCfg.EncoderConfig.EncodeLevel = zapcore.CapitalColorLevelEncoder
	} else {
		zapCfg = zap.NewProductionConfig()
	}

	zapCfg.Level = zap.NewAtomicLevelAt(cfg.LogLevel)
	zapCfg.EncoderConfig.TimeKey = "timestamp"
	zapCfg.EncoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder
	zapCfg.EncoderConfig.CallerKey = "caller"

	logger, err := zapCfg.Build(zap.AddCallerSkip(1))
	if err != nil {
		return nil, err
	}

	logger = logger.With(
		zap.String("service", cfg.ServiceName),
		zap.String("version", cfg.Version),
		zap.String("environment", cfg.Environment),
	)

	return &Logger{l: logger}, nil
}

// With adds fields to the logger context.
func (l *Logger) With(args ...interface{}) *Logger {
	fields := l.toZapFields(args...)
	return &Logger{l: l.l.With(fields...)}
}

// Debug logs a message at the debug level.
func (l *Logger) Debug(msg string, args ...interface{}) {
	fields := l.toZapFields(args...)
	l.l.Debug(msg, fields...)
}

// Info logs a message at the info level.
func (l *Logger) Info(msg string, args ...interface{}) {
	fields := l.toZapFields(args...)
	l.l.Info(msg, fields...)
}

// Warn logs a message at the warn level.
func (l *Logger) Warn(msg string, args ...interface{}) {
	fields := l.toZapFields(args...)
	l.l.Warn(msg, fields...)
}

// Error logs a message at the error level.
func (l *Logger) Error(msg string, err error, args ...interface{}) {
	allArgs := append(args, "error", err)
	fields := l.toZapFields(allArgs...)
	l.l.Error(msg, fields...)
}

// Fatal logs a message at the fatal level.
func (l *Logger) Fatal(msg string, err error, args ...interface{}) {
	allArgs := append(args, "error", err)
	fields := l.toZapFields(allArgs...)
	l.l.Fatal(msg, fields...)
}

// WithContext adds the logger to the context.
func ToContext(ctx context.Context, logger *Logger) context.Context {
	return context.WithValue(ctx, ctxKey{}, logger)
}

// FromContext retrieves the logger from the context.
func FromContext(ctx context.Context) *Logger {
	if logger, ok := ctx.Value(ctxKey{}).(*Logger); ok {
		return logger
	}
	return defaultLogger
}

// toZapFields converts the key-value pairs to zap fields.
func (l *Logger) toZapFields(args ...interface{}) []zap.Field {
	if len(args)%2 != 0 {
		l.l.Error("Invalid key-value pairs for logging. Must be an even number of args.",
			zap.Any("args", args),
		)
		return []zap.Field{zap.Any("logging_error", "odd number of arguments provided")}
	}

	fields := make([]zap.Field, 0, len(args)/2)
	for i := 0; i < len(args); i += 2 {
		key, ok := args[i].(string)
		if !ok {
			l.l.Error("Log key is not a string", zap.Any("key", args[i]))
			continue
		}
		switch v := args[i+1].(type) {
		case string:
			fields = append(fields, zap.String(key, v))
		case int:
			fields = append(fields, zap.Int(key, v))
		case int64:
			fields = append(fields, zap.Int64(key, v))
		case float64:
			fields = append(fields, zap.Float64(key, v))
		case bool:
			fields = append(fields, zap.Bool(key, v))
		case time.Time:
			fields = append(fields, zap.Time(key, v))
		case time.Duration:
			fields = append(fields, zap.Duration(key, v))
		case error:
			fields = append(fields, zap.Error(v))
		default:
			fields = append(fields, zap.Any(key, v))
		}
	}

	return fields
}
