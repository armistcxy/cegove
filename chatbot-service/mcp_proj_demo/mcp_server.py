from typing import Optional, List, Dict

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("movies")

MOVIE_API_BASE = "https://movies.cegove.cloud"
USER_AGENT = "cegove/movie_mcp"


async def make_movie_request(path: str, params: dict):
    async with httpx.AsyncClient(
        base_url=MOVIE_API_BASE,
        headers={"User-Agent": USER_AGENT},
        timeout=10.0,
    ) as client:
        response = await client.get(path, params=params)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_movies(
    year: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict:
    """
    Get movies with simple pagination.
    Supports filtering by year.
    """
    params = {
        "page": page,
        "page_size": page_size,
    }

    if year:
        params["year"] = year

    return await make_movie_request("/api/v1/movies/", params)


if __name__ == "__main__":
    mcp.run()
