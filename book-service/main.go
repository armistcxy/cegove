package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"os"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/spf13/cast"
)

func main() {
	dsn := os.Getenv("PG_DSN")
	pool, err := pgxpool.New(context.Background(), dsn)
	if err != nil {
		panic(err)
	}
	defer pool.Close()

	bookRepository := NewBookRepository(pool)

	http.HandleFunc("GET /api/v1/books/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		book, err := bookRepository.GetBook(cast.ToInt(id))

		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(book); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
	})

	http.HandleFunc("GET /api/v1/books", func(w http.ResponseWriter, r *http.Request) {
		page := r.URL.Query().Get("page")
		if page == "" {
			page = "1"
		}
		size := r.URL.Query().Get("size")
		if size == "" {
			size = "10"
		}
		offset := (cast.ToInt(page) - 1) * cast.ToInt(size)

		books, err := bookRepository.ListBooks(offset, cast.ToInt(size))
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(books); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
	})

	http.HandleFunc("POST /api/v1/books", func(w http.ResponseWriter, r *http.Request) {
		book := &Book{}
		if err := json.NewDecoder(r.Body).Decode(book); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		if err := bookRepository.InsertBook(book); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
	})

	http.HandleFunc("PUT /api/v1/books/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		book := &Book{ID: cast.ToInt(id)}
		if err := json.NewDecoder(r.Body).Decode(book); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		if err := bookRepository.UpdateBook(book); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
	})

	http.HandleFunc("DELETE /api/v1/books/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		if err := bookRepository.DeleteBook(cast.ToInt(id)); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
	})

	log.Println("Starting server")
	log.Println("Server is listening on port 8080")
	http.ListenAndServe(":8080", nil)
}
