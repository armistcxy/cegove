package httphelp

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/go-chi/chi/v5"
)

// Server is the HTTP server
type Server struct {
	Router          *chi.Mux
	GracefulTimeout time.Duration
}

// DefaultGracefulTimeout is the default graceful timeout for the server
const DefaultGracefulTimeout = 15 * time.Second

// NewServer creates a new server.
//
// Allow passing in middlewares to be applied to all routes (global middlewares).
// This is useful for logging, tracing, etc.
//
// Recovery middleware is forced to ensure server's availability.
// (This middleware is automatically added to the server)
func NewServer(middlewares ...func(http.Handler) http.Handler) *Server {
	mux := chi.NewMux()
	// Recovery middleware must be the first one
	mux.Use(RecoveryMiddleware)
	mux.Use(middlewares...)

	return &Server{
		Router:          mux,
		GracefulTimeout: DefaultGracefulTimeout,
	}
}

// RegisterRouter registers a router
func (s *Server) RegisterRouter(prefix string, r *Router) {
	s.Router.Mount(prefix, r.r)
}

// ListenAndServe starts the server
func (s *Server) ListenAndServe(addr string) error {
	server := &http.Server{
		Addr:    addr,
		Handler: s.Router,
	}
	errChan := make(chan error)

	go func() {
		log.Printf("Server is listening on %s\n", server.Addr)

		// Walk through all routes
		err := chi.Walk(s.Router, func(method string, route string, handler http.Handler, middlewares ...func(http.Handler) http.Handler) error {
			log.Printf("%s%-6s%s %s\n", methodColor(method), method, reset, route)
			return nil
		})
		if err != nil {
			log.Printf("Error walking routes: %v\n", err)
		}

		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			errChan <- err
		}
	}()

	stopChan := make(chan os.Signal, 1)
	signal.Notify(stopChan, syscall.SIGINT, syscall.SIGTERM)

	select {
	case err := <-errChan:
		return err
	case sig := <-stopChan:
		log.Printf("Shutdown signal received: %s. Starting graceful shutdown...\n", sig)
		ctx, cancel := context.WithTimeout(context.Background(), s.GracefulTimeout)
		defer cancel()

		if err := server.Shutdown(ctx); err != nil {
			log.Printf("Error shutting down server: %v\n", err)
			return err
		}
		log.Printf("Server gracefully stopped\n")
	}

	return nil
}

// Colors for the methods
const (
	green   = "\033[32m"
	cyan    = "\033[36m"
	yellow  = "\033[33m"
	red     = "\033[31m"
	blue    = "\033[34m"
	magenta = "\033[35m"

	reset = "\033[0m"
)

// methodColor returns the color for the method
func methodColor(method string) string {
	switch method {
	case http.MethodGet:
		return green
	case http.MethodPost:
		return cyan
	case http.MethodPut:
		return yellow
	case http.MethodDelete:
		return red
	case http.MethodTrace:
		return blue
	case http.MethodConnect:
		return magenta
	default:
		return reset
	}
}
