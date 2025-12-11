package httphelp

import (
	"net/http"

	"github.com/go-chi/chi/v5"
)

// Router is the HTTP router
type Router struct {
	middlewares []func(http.Handler) http.Handler
	r           chi.Router
}

// NewRouter creates a new router
func NewRouter(middlewares ...func(http.Handler) http.Handler) *Router {
	return &Router{
		middlewares: middlewares,
		r:           chi.NewRouter(),
	}
}

// RegisterHandler registers a handler
func (rt *Router) RegisterHandler(method string, pattern string, handler http.Handler) {
	rt.r.With(rt.middlewares...).Method(method, pattern, handler)
}

// RegisterHandlerFunc registers a handler function
func (rt *Router) RegisterHandlerFunc(method string, pattern string, handler http.HandlerFunc) {
	rt.RegisterHandler(method, pattern, handler)
}
