package httphelp

import (
	"fmt"
	"log"
	"net/http"
	"runtime/debug"
	"strconv"

	"github.com/felixge/httpsnoop"
	"github.com/prometheus/client_golang/prometheus"
)

// RecoveryMiddleware recovers from panics
func RecoveryMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if err := recover(); err != nil {
				w.Header().Set("Connection", "close")
				log.Println(err)
				debug.PrintStack()
				EncodeJSONError(w, r, http.StatusInternalServerError, fmt.Errorf("%v", err))
			}
		}()
		next.ServeHTTP(w, r)
	})
}

type HTTPMetrics struct {
	Requests *prometheus.CounterVec
	Duration *prometheus.HistogramVec
}

func NewHTTPMetrics(reg *prometheus.Registry, prefix string) *HTTPMetrics {
	m := &HTTPMetrics{
		Requests: prometheus.NewCounterVec(
			prometheus.CounterOpts{
				Namespace: prefix,
				Name:      "http_requests_total",
				Help:      "Total HTTP requests",
			},
			[]string{"code", "method", "path"},
		),
		Duration: prometheus.NewHistogramVec(
			prometheus.HistogramOpts{
				Namespace: prefix,
				Name:      "http_request_duration_seconds",
				Help:      "HTTP request duration in seconds",
				Buckets:   prometheus.DefBuckets,
			},
			[]string{"method", "path"},
		),
	}

	reg.MustRegister(m.Requests, m.Duration)
	return m
}

func (m *HTTPMetrics) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		metrics := httpsnoop.CaptureMetrics(next, w, r)
		path := r.URL.Path
		m.Requests.WithLabelValues(strconv.Itoa(metrics.Code), r.Method, path).Inc()
		m.Duration.WithLabelValues(r.Method, path).Observe(metrics.Duration.Seconds())
	})
}
