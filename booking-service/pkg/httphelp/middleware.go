package httphelp

import (
	"fmt"
	"log"
	"net/http"
	"runtime/debug"
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
