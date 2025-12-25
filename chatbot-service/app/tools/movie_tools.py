# app/tools/movie_tools.py
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.services.api_client import api_client

# Tool definitions for OpenAI/Groq format
MOVIE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_movies",
            "description": "Search for movies by name or keyword. Use when user asks about a specific movie by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Movie name or search term"},
                    "limit": {"type": "integer", "description": "Max results to return", "default": 5}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_movies_list",
            "description": "Get list of movies with optional filters. Use for browsing, recommendations, or when user asks 'what movies are available'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "genre": {"type": "string", "description": "Genre filter (Action, Comedy, Drama, Horror, Sci-Fi, etc.)"},
                    "year": {"type": "string", "description": "Release year filter"},
                    "sort_by": {"type": "string", "enum": ["imdb_rating", "released_year"], "description": "Sort order"},
                    "limit": {"type": "integer", "description": "Max results", "default": 5}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_movie_details",
            "description": "Get detailed information about a specific movie by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "movie_id": {"type": "integer", "description": "The movie ID"}
                },
                "required": ["movie_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_showtimes",
            "description": "Get available showtimes. Can filter by movie, cinema, or date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "movie_id": {"type": "integer", "description": "Filter by movie ID"},
                    "cinema_id": {"type": "integer", "description": "Filter by cinema ID"},
                    "date": {"type": "string", "description": "Date in YYYY-MM-DD format"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_cinemas",
            "description": "Search for cinemas by name or city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Cinema name or city to search"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_cinemas_in_city",
            "description": "Get all cinemas in a specific city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name (e.g., 'Ha Noi', 'Ho Chi Minh')"}
                },
                "required": ["city"]
            }
        }
    }
]


def get_today_date() -> str:
    """Get today's date in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%d")


async def execute_tool(tool_name: str, tool_input: Dict) -> Dict[str, Any]:
    """
    Execute a tool and return results with structured metadata.
    Returns: {data, chips, error?}
    """
    try:
        if tool_name == "search_movies":
            movies = await api_client.search_movies(
                query=tool_input["query"],
                limit=tool_input.get("limit", 5)
            )
            return {
                "data": movies,
                "chips": [
                    {"type": "movie", "id": str(m.get("id")), "label": m.get("series_title", m.get("title", "Unknown"))}
                    for m in movies[:5]
                ]
            }

        elif tool_name == "get_movies_list":
            result = await api_client.get_movies(
                page=1,
                page_size=tool_input.get("limit", 5),
                genre=tool_input.get("genre"),
                year=tool_input.get("year"),
                sort_by=tool_input.get("sort_by", "imdb_rating")
            )
            movies = result.get("items", [])
            return {
                "data": movies,
                "chips": [
                    {"type": "movie", "id": str(m.get("id")), "label": m.get("series_title", m.get("title", "Unknown"))}
                    for m in movies[:5]
                ]
            }

        elif tool_name == "get_movie_details":
            movie = await api_client.get_movie_detail(tool_input["movie_id"])
            if movie:
                return {
                    "data": movie,
                    "chips": [
                        {"type": "action", "action": "showtimes", "movie_id": tool_input["movie_id"], "label": "Xem lich chieu"},
                    ]
                }
            return {"data": None, "chips": [], "error": "Movie not found"}

        elif tool_name == "get_showtimes":
            showtimes = await api_client.get_showtimes(
                movie_id=tool_input.get("movie_id"),
                cinema_id=tool_input.get("cinema_id"),
                date=tool_input.get("date")
            )

            # Create chips for showtimes - these will navigate to seat selection
            chips = []
            for st in showtimes[:8]:
                start_time = st.get("start_time", "")
                if isinstance(start_time, str) and len(start_time) >= 5:
                    time_str = start_time[:5]
                else:
                    time_str = str(start_time)

                price = st.get("base_price", 0)
                cinema_name = st.get("cinema_name", "")

                label = f"{time_str}"
                if cinema_name:
                    label = f"{cinema_name} - {time_str}"
                if price:
                    label += f" ({price:,.0f}d)"

                chips.append({
                    "type": "showtime",
                    "id": str(st.get("id")),
                    "label": label,
                    "cinema_id": st.get("cinema_id"),
                    "movie_id": st.get("movie_id")
                })

            return {
                "data": showtimes,
                "chips": chips
            }

        elif tool_name == "search_cinemas":
            cinemas = await api_client.search_cinemas(tool_input["query"])
            return {
                "data": cinemas,
                "chips": [
                    {"type": "cinema", "id": str(c.get("id")), "label": c.get("name", "Unknown")}
                    for c in cinemas[:5]
                ]
            }

        elif tool_name == "get_cinemas_in_city":
            cinemas = await api_client.get_cinemas(city=tool_input["city"])
            return {
                "data": cinemas,
                "chips": [
                    {"type": "cinema", "id": str(c.get("id")), "label": c.get("name", "Unknown")}
                    for c in cinemas[:5]
                ]
            }

        else:
            return {"data": None, "chips": [], "error": f"Unknown tool: {tool_name}"}

    except Exception as e:
        print(f"[movie_tools] Error executing {tool_name}: {e}")
        return {"data": None, "chips": [], "error": str(e)}
