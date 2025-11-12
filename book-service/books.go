package main

import (
	"context"

	"github.com/jackc/pgx/v5/pgxpool"
)

type Book struct {
	ID   int    `json:"id"`
	Name string `json:"name"`
}

type BookRepository struct {
	db *pgxpool.Pool
}

func NewBookRepository(db *pgxpool.Pool) *BookRepository {
	return &BookRepository{db: db}
}

func (b *BookRepository) GetBook(id int) (*Book, error) {
	row := b.db.QueryRow(context.Background(), "SELECT id, name FROM books WHERE id = $1", id)
	book := &Book{}
	if err := row.Scan(&book.ID, &book.Name); err != nil {
		return nil, err
	}

	return book, nil
}

func (b *BookRepository) ListBooks(offset int, limit int) ([]Book, error) {
	rows, err := b.db.Query(context.Background(), "SELECT id, name FROM books LIMIT $1 OFFSET $2", limit, offset)
	if err != nil {
		return nil, err
	}
	books := []Book{}
	for rows.Next() {
		book := Book{}
		if err := rows.Scan(&book.ID, &book.Name); err != nil {
			return nil, err
		}
		books = append(books, book)
	}

	return books, nil
}

func (b *BookRepository) InsertBook(book *Book) error {
	_, err := b.db.Exec(context.Background(), "INSERT INTO books (id, name) VALUES ($1, $2)", book.ID, book.Name)
	if err != nil {
		return err
	}
	return nil
}

func (b *BookRepository) UpdateBook(book *Book) error {
	_, err := b.db.Exec(context.Background(), "UPDATE books SET name = $1 WHERE id = $2", book.Name, book.ID)
	if err != nil {
		return err
	}
	return nil
}

func (b *BookRepository) DeleteBook(id int) error {
	_, err := b.db.Exec(context.Background(), "DELETE FROM books WHERE id = $1", id)
	if err != nil {
		return err
	}
	return nil
}
