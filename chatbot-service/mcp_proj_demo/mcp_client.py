import asyncio
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession


async def main():
    server_params = StdioServerParameters(
        command="../.venv/bin/python",
        args=["mcp_server.py"],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print("✅ MCP connected")

            result = await session.call_tool(
                "get_movies",
                {
                    "page": 1,
                    "page_size": 20,
                    "year": "2020",
                },
            )

            print("\n🎬 Movies result:")
            print(result)


if __name__ == "__main__":
    asyncio.run(main())
