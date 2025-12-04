package httphelp

import (
	"encoding/json"
	"errors"
	"net/http"
	"strings"
)

// EncodeJSON encodes v to JSON and writes it to w.
func EncodeJSON[T any](w http.ResponseWriter, r *http.Request, status int, v T) error {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	return json.NewEncoder(w).Encode(v)
}

// EncodeJSONError encodes err to JSON and writes it to w.
func EncodeJSONError(w http.ResponseWriter, r *http.Request, status int, err error) error {
	errBody := map[string]any{
		"error": err.Error(),
	}
	return EncodeJSON(w, r, status, errBody)
}

// DecodeJSON decodes the request body to v.
func DecodeJSON[T any](r *http.Request) (T, error) {
	if !strings.HasPrefix(r.Header.Get("Content-Type"), "application/json") {
		return *new(T), ErrInvalidContentType
	}

	var v T
	err := json.NewDecoder(r.Body).Decode(&v)
	return v, err
}

var ErrInvalidContentType = errors.New("invalid content type")
