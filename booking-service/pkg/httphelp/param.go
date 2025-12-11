package httphelp

import (
	"fmt"
	"net/http"
	"strconv"
	"strings"
)

// PaginationParam is the pagination parameter
//
// Example: http://localhost:8080/api/users?page=2&size=15
type PaginationParam struct {
	Page     uint64
	PageSize uint64
}

// SortParam is the sort parameter
//
// Example: http://localhost:8080/api/users?sort=id:asc&sort=name:desc
type SortParam struct {
	Field string
	IsAsc bool
}

// SearchParam is the search parameter
//
// Example: http://localhost:8080/api/users?search=John
type SearchParam struct {
	Term string
}

// TypicalListQueryParam is the typical query parameter for list
type TypicalListQueryParam struct {
	Pagination *PaginationParam
	Sort       []SortParam
	Search     *SearchParam
}

// GetTypicalListQueryParam returns the typical query parameter for list
func GetTypicalListQueryParam(r *http.Request) (*TypicalListQueryParam, error) {
	paginationParam, err := GetPaginationParam(r)
	if err != nil {
		return nil, err
	}

	sortParams, err := GetSortParams(r)
	if err != nil {
		return nil, err
	}

	searchParam, err := GetSearchParam(r)
	if err != nil {
		return nil, err
	}

	return &TypicalListQueryParam{
		Pagination: paginationParam,
		Sort:       sortParams,
		Search:     searchParam,
	}, nil
}

// GetPaginationParam returns the pagination parameter
func GetPaginationParam(r *http.Request) (*PaginationParam, error) {
	q := r.URL.Query()

	var (
		page uint64
		size uint64
		err  error
	)

	if q.Get("page") == "" {
		page = 1
	} else {
		page, err = strconv.ParseUint(q.Get("page"), 10, 64)
		if err != nil {
			return nil, fmt.Errorf("invalid page number: %s", q.Get("page"))
		}
	}

	if q.Get("size") == "" {
		size = 10
	} else {
		size, err = strconv.ParseUint(q.Get("size"), 10, 64)
		if err != nil {
			return nil, fmt.Errorf("invalid page size: %s", q.Get("size"))
		}
	}

	return &PaginationParam{
		Page:     page,
		PageSize: size,
	}, nil
}

// GetSortParams returns the sort parameters
func GetSortParams(r *http.Request) ([]SortParam, error) {
	q := r.URL.Query()

	var sortParams []SortParam

	for _, sort := range q["sort"] {
		parts := strings.Split(sort, ":")
		if len(parts) != 2 {
			return nil, fmt.Errorf("invalid sort parameter: %s", sort)
		}

		isAsc := true
		if parts[1] == "desc" {
			isAsc = false
		}
		sortParams = append(sortParams, SortParam{
			Field: parts[0],
			IsAsc: isAsc,
		})
	}

	return sortParams, nil
}

// GetSearchParam returns the search parameter
func GetSearchParam(r *http.Request) (*SearchParam, error) {
	q := r.URL.Query()

	return &SearchParam{
		Term: q.Get("search"),
	}, nil
}
