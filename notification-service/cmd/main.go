package main

import (
	"context"
	"fmt"
	"net"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/propagation"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/reflection"

	notificationpb "github.com/armistcxy/cegove/notification-service/api"
	"github.com/armistcxy/cegove/notification-service/internal/notify"
	"github.com/armistcxy/cegove/notification-service/pkg/email"
	"github.com/armistcxy/cegove/notification-service/pkg/httphelp"
	"github.com/armistcxy/cegove/notification-service/pkg/logging"
	"github.com/armistcxy/cegove/notification-service/pkg/sms"
	"github.com/armistcxy/cegove/notification-service/pkg/tracing"

	httpSwagger "github.com/swaggo/http-swagger"
)

func main() {
	// Initialize logger
	logger, err := logging.NewLogger(logging.Config{
		ServiceName: "notification-service",
		Version:     "1.0.0",
		Environment: "production",
	})
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to initialize logger: %v\n", err)
		os.Exit(1)
	}
	otel.SetTextMapPropagator(
		propagation.NewCompositeTextMapPropagator(
			propagation.TraceContext{},
			propagation.Baggage{},
		),
	)
	// Initialize Jaeger tracing
	jaegerEndpoint := os.Getenv("JAEGER_ENDPOINT")
	if jaegerEndpoint == "" {
		jaegerEndpoint = "localhost:4317" // Default Jaeger gRPC endpoint
	}

	ctx := context.Background()
	tp, err := tracing.InitJaegerTracer(ctx, "notification-service", jaegerEndpoint)
	if err != nil {
		logger.Fatal("failed to initialize jaeger tracer", err)
	}
	defer func() {
		if err := tp.Shutdown(ctx); err != nil {
			logger.Error("error shutting down trace provider", err)
		}
	}()

	// Set the global tracer provider
	otel.SetTracerProvider(tp)

	// Get Mailgun configuration from environment
	mailgunDomain := os.Getenv("MAILGUN_DOMAIN")
	mailgunAPIKey := os.Getenv("MAILGUN_API_KEY")
	mailgunDefaultFrom := os.Getenv("MAILGUN_DEFAULT_FROM")

	if mailgunDomain == "" || mailgunAPIKey == "" {
		logger.Fatal("MAILGUN_DOMAIN and MAILGUN_API_KEY environment variables are required", nil)
	}

	// Initialize email provider (Mailgun)
	emailProvider, err := email.NewMailgunProvider(mailgunDomain, mailgunAPIKey, mailgunDefaultFrom)
	if err != nil {
		logger.Fatal("failed to initialize email provider", err)
	}

	// // Get Twilio configuration from environment
	// twilioAPIKey := os.Getenv("TWILIO_API_KEY")
	// twilioAPISecret := os.Getenv("TWILIO_API_SECRET")
	// twilioFromPhone := os.Getenv("TWILIO_FROM_PHONE")

	// if twilioAPIKey == "" || twilioAPISecret == "" || twilioFromPhone == "" {
	// 	logger.Fatal("TWILIO_API_KEY, TWILIO_API_SECRET, and TWILIO_FROM_PHONE environment variables are required", nil)
	// }

	// // Initialize SMS provider (Twilio)
	// smsProvider := sms.NewTwilioSender(twilioAPIKey, twilioAPISecret, twilioFromPhone)

	vonageAPIKey := os.Getenv("VONAGE_API_KEY")
	vonageAPISecret := os.Getenv("VONAGE_API_SECRET")
	vonageFrom := "Cegove"

	if vonageAPIKey == "" || vonageAPISecret == "" {
		logger.Fatal("VONAGE_API_KEY and VONAGE_API_SECRET environment variables are required", nil)
	}

	// Initialize SMS provider (Vonage)
	smsProvider := sms.NewVonageSender(vonageAPIKey, vonageAPISecret, vonageFrom)

	// Create gRPC server
	grpcServer := grpc.NewServer()

	// Register NotificationService implementation
	svc := notify.NewNotificationServiceImpl(emailProvider, smsProvider, logger)
	notificationpb.RegisterNotificationServiceServer(grpcServer, svc)
	reflection.Register(grpcServer)

	// Start gRPC server in a goroutine
	go func() {
		listener, err := net.Listen("tcp", ":50051")
		if err != nil {
			logger.Fatal("failed to listen on gRPC port", err)
		}
		logger.Info("gRPC server listening on port 50051")
		if err := grpcServer.Serve(listener); err != nil {
			logger.Fatal("gRPC server error", err)
		}
	}()

	// Create HTTP gateway
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	// Get tracer from the global provider
	tracer := otel.Tracer("notification-service")

	srv := httphelp.NewServer(tracing.HTTPMiddleware(tracer))
	mux := runtime.NewServeMux()

	// Register gRPC gateway
	opts := []grpc.DialOption{grpc.WithTransportCredentials(insecure.NewCredentials())}
	if err := notificationpb.RegisterNotificationServiceHandlerFromEndpoint(ctx, mux, "localhost:50051", opts); err != nil {
		logger.Fatal("failed to register gateway handler", err)
	}

	srv.Router.Mount("/", mux)
	srv.Router.HandleFunc("/swagger/doc.json", func(w http.ResponseWriter, r *http.Request) {
		http.ServeFile(w, r, "docs/notification_service.swagger.json")
	})
	srv.Router.Handle("/swagger/*",
		httpSwagger.Handler(httpSwagger.URL("/swagger/doc.json")),
	)

	logger.Info("HTTP gateway server listening on port 8080")

	// Start HTTP server in a goroutine
	go func() {
		if err := srv.ListenAndServe(":8080"); err != nil {
			logger.Fatal("HTTP server error", err)
		}
	}()

	// Wait for shutdown signal
	<-ctx.Done()
	logger.Info("Shutting down servers...")
	grpcServer.GracefulStop()
	logger.Info("Shutdown complete")
}
