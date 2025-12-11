package main

//go:generate swag init -g cmd/main.go -o docs

//go:generate swag init -g cmd/main.go -o docs

// @title Booking Service API
// @version 1.0
// @description This is the booking service API.
// @contact.name API Support
// @contact.email support@example.com
// @host localhost:8080
// @BasePath /api

import (
	"context"
	"fmt"
	"log"
	"net/url"
	"os"
	"strings"

	"github.com/armistcxy/cegove/booking-service/internal/handler"
	"github.com/armistcxy/cegove/booking-service/pkg/config"
	"github.com/armistcxy/cegove/booking-service/pkg/httphelp"
	"github.com/armistcxy/cegove/booking-service/pkg/logging"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/collectors"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/rs/cors"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/spf13/viper"
	"go.uber.org/zap/zapcore"

	_ "github.com/armistcxy/cegove/booking-service/docs"
	_ "github.com/prometheus/client_golang/prometheus/promauto"

	httpSwagger "github.com/swaggo/http-swagger"
)

func main() {
	var (
		consulAddr = os.Getenv("CONSUL_ADDR")
		consulUser = os.Getenv("CONSUL_USER")
		consulPass = os.Getenv("CONSUL_PASSWORD")
	)

	log.Printf("Just for testing")

	consulLoader, err := config.NewConsulConfigLoader(config.ConsulLoaderConfig{
		ConsulAddr: consulAddr,
		User:       consulUser,
		Password:   consulPass,
	})
	if err != nil {
		log.Fatalf("failed to create consul loader: %v", err)
	}

	reg := prometheus.NewRegistry()
	reg.MustRegister(
		collectors.NewProcessCollector(collectors.ProcessCollectorOpts{}),
		collectors.NewGoCollector(),
	)
	httpMetrics := httphelp.NewHTTPMetrics(reg, "booking-service")

	// CORS middleware
	c := cors.New(cors.Options{
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"*"},
		AllowCredentials: true,
		AllowOriginFunc:  isAllowedOrigin,
	})
	server := httphelp.NewServer(c.Handler, httpMetrics.Middleware)
	server.Router.Handle("/metrics", promhttp.HandlerFor(reg, promhttp.HandlerOpts{}))

	remoteConfigKeys := []string{
		"infra/postgres.toml",
		"service/booking-service.toml",
	}
	err = consulLoader.LoadConfigsToGlobal(context.Background(), remoteConfigKeys...)
	if err != nil {
		log.Fatalf("failed to load config from consul: %v", err)
	}

	env := viper.GetString("env")

	logger, err := logging.NewLogger(logging.Config{
		ServiceName: "booking-service",
		Version:     "1.0.0",
		Environment: env,
		LogLevel:    zapcore.DebugLevel,
	})
	if err != nil {
		log.Fatalf("failed to create logger: %v", err)
	}

	connString := fmt.Sprintf("postgres://%s:%s@%s:%s/%s",
		viper.GetString("postgres.user"),
		viper.GetString("postgres.password"),
		viper.GetString("postgres.host"),
		viper.GetString("postgres.port"),
		viper.GetString("postgres.database"),
	)
	pool, err := pgxpool.New(context.Background(), connString)
	if err != nil {
		log.Fatalf("failed to connect to database: %v", err)
	}

	bookingRouter := handler.NewBookingRouter(pool, logger)
	server.RegisterRouter("/api", bookingRouter.Router)

	// Swagger UI
	server.Router.Handle("/api/swagger/*", httpSwagger.Handler(
		httpSwagger.URL("/api/swagger/doc.json"),
	))

	// Remove duplicate Swagger UI registration

	if err := server.ListenAndServe(":8080"); err != nil {
		log.Fatalf("failed to start server: %v", err)
	}
}

func isAllowedOrigin(origin string) bool {
	u, _ := url.Parse(origin)
	host := u.Host
	if strings.Contains(host, "localhost") || strings.Contains(host, "cegove.cloud") {
		return true
	}
	return false
}
