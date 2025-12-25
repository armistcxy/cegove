package tracing

import (
	"context"
	"fmt"
	"net/http"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/codes"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.31.0"
	"go.opentelemetry.io/otel/trace"
)

// InitJaegerTracer initializes a Jaeger tracer with OTLP gRPC exporter
func InitJaegerTracer(ctx context.Context, serviceName string, jaegerEndpoint string) (*sdktrace.TracerProvider, error) {
	// Create the OTLP gRPC exporter with insecure connection for internal use
	exporter, err := otlptracegrpc.New(ctx,
		otlptracegrpc.WithEndpoint(jaegerEndpoint),
		otlptracegrpc.WithInsecure(),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to create otlp exporter: %w", err)
	}

	// Create the resource
	res, err := resource.New(ctx,
		resource.WithAttributes(
			semconv.ServiceName(serviceName),
		),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to create resource: %w", err)
	}

	// Create the tracer provider
	tp := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exporter),
		sdktrace.WithResource(res),
	)

	return tp, nil
}

// HTTPMiddleware creates a span for every HTTP request
func HTTPMiddleware(tracer trace.Tracer) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			ctx := otel.GetTextMapPropagator().Extract(r.Context(), propagation.HeaderCarrier(r.Header))

			ctx, span := tracer.Start(ctx, r.Method+" "+r.URL.Path,
				trace.WithAttributes(
					attribute.String("http.method", r.Method),
					attribute.String("http.url", r.URL.String()),
					attribute.String("http.target", r.URL.Path),
					attribute.String("http.host", r.Host),
					attribute.String("http.scheme", r.URL.Scheme),
				),
			)
			defer span.End()

			// Create a response writer wrapper to capture status code
			wrapped := &responseWriter{ResponseWriter: w}

			// Serve the request with the new context
			r = r.WithContext(ctx)
			next.ServeHTTP(wrapped, r)

			// Set span attributes based on response
			span.SetAttributes(
				attribute.Int("http.status_code", wrapped.statusCode),
			)

			// Set span status based on HTTP status code
			if wrapped.statusCode >= 400 {
				if wrapped.statusCode >= 500 {
					span.SetStatus(codes.Error, http.StatusText(wrapped.statusCode))
				} else {
					span.SetStatus(codes.Ok, http.StatusText(wrapped.statusCode))
				}
			}
		})
	}
}

// responseWriter wraps http.ResponseWriter to capture status code
type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

func (rw *responseWriter) Write(b []byte) (int, error) {
	if rw.statusCode == 0 {
		rw.statusCode = http.StatusOK
	}
	return rw.ResponseWriter.Write(b)
}
