package httphelp

import (
	"fmt"
	"log"
	"math"
	"net/http"
	"runtime/debug"
	"sort"
	"strconv"
	"sync"
	"time"

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

type MetricsCollector struct {
	mu           sync.RWMutex
	statusCounts map[int]int64
	latencies    []time.Duration
}

func NewMetricsCollector() *MetricsCollector {
	return &MetricsCollector{
		statusCounts: make(map[int]int64),
		latencies:    make([]time.Duration, 0),
	}
}

func (m *MetricsCollector) Record(statusCode int, duration time.Duration) {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.statusCounts[statusCode]++
	m.latencies = append(m.latencies, duration)
}

func (m *MetricsCollector) GetSnapshot() map[string]interface{} {
	m.mu.RLock()
	defer m.mu.RUnlock()

	tempLatencies := make([]time.Duration, len(m.latencies))
	copy(tempLatencies, m.latencies)

	sort.Slice(tempLatencies, func(i, j int) bool {
		return tempLatencies[i] < tempLatencies[j]
	})

	count := len(tempLatencies)

	getPercentile := func(p float64) time.Duration {
		if count == 0 {
			return 0
		}
		index := int(math.Ceil(float64(count)*p)) - 1
		if index < 0 {
			index = 0
		}
		if index >= count {
			index = count - 1
		}
		return tempLatencies[index]
	}

	stats := map[string]interface{}{
		"total_requests": count,
		"status_counts":  m.statusCounts,
		"latency": map[string]string{
			"p50": getPercentile(0.50).String(),
			"p90": getPercentile(0.90).String(),
			"p95": getPercentile(0.95).String(),
			"p99": getPercentile(0.99).String(),
			"max": getPercentile(1.00).String(),
		},
	}

	return stats
}

func (m *MetricsCollector) Reset() {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.statusCounts = make(map[int]int64)
	m.latencies = make([]time.Duration, 0)
}

var (
	httpRequestsTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "http_requests_total",
			Help: "Total number of HTTP requests",
		},
		[]string{"code", "method", "path"},
	)

	httpRequestDuration = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name: "http_request_duration_seconds",
			Help: "Duration of HTTP requests in seconds",
			// Định nghĩa các 'thùng' thời gian (Buckets) để đo lường.
			// Đơn vị là giây. Ví dụ: .005 là 5ms, .1 là 100ms, 1 là 1s.
			Buckets: []float64{.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10},
		},
		[]string{"method", "path"},
	)
)

func init() {
	prometheus.MustRegister(httpRequestsTotal)
	prometheus.MustRegister(httpRequestDuration)
}

func (m *MetricsCollector) MetricRetrieveMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		metrics := httpsnoop.CaptureMetrics(next, w, r)
		path := r.URL.Path
		statusCode := strconv.Itoa(metrics.Code)
		httpRequestsTotal.WithLabelValues(statusCode, r.Method, path).Inc()
		httpRequestDuration.WithLabelValues(r.Method, path).Observe(metrics.Duration.Seconds())
	})
}
