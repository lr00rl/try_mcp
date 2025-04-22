from typing import Annotated
import httpx
import sys
import logging
import asyncio

from mcp.shared.exceptions import McpError
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.tcp import tcp_server
from mcp.types import (
    ErrorData,
    GetPromptResult,
    Prompt,
    PromptMessage,
    TextContent,
    Tool,
    INVALID_PARAMS,
    INTERNAL_ERROR,
)
from pydantic import BaseModel, Field

# 设置日志记录到文件
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='mcp_server.log',
    filemode='w'
)
logger = logging.getLogger("ipcheck_mcp")

DEFAULT_USER_AGENT = "ModelContextProtocol/1.0 (IP Checker)"

class IPCheckOptions(BaseModel):
    """Parameters for IP check tool."""
    format: Annotated[
        str,
        Field(
            default="text",
            description="Response format. Options: 'text' (plain text), 'json' (includes additional data)"
        ),
    ]

async def get_ip_address(format_type: str = "text", user_agent: str = DEFAULT_USER_AGENT) -> str:
    """Fetch the server's public IP address from ifconfig.me"""
    url = "https://ifconfig.me"
    if format_type == "json":
        url += "/all.json"

    logger.info(f"Fetching IP from {url}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                follow_redirects=True,
                headers={"User-Agent": user_agent},
                timeout=10,
            )

        if response.status_code >= 400:
            error_msg = f"Failed to fetch IP address - status code {response.status_code}"
            logger.error(error_msg)
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=error_msg))

        logger.info("Successfully fetched IP address")
        return response.text
    except httpx.HTTPError as e:
        error_msg = f"Failed to fetch IP address: {e!r}"
        logger.error(error_msg)
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=error_msg))

# async def serve(custom_user_agent: str | None = None) -> None:
#     """Run the IP check MCP server."""
#     try:
#         server = Server("ipcheck_mcp")
#         user_agent = custom_user_agent or DEFAULT_USER_AGENT
#
#         logger.info(f"Starting MCP server with user agent: {user_agent}")
#
#         @server.list_tools()
#         async def list_tools() -> list[Tool]:
#             logger.info("list_tools called")
#             return [
#                 Tool(
#                     name="ipcheck",
#                     description="Checks the server's public IP address by querying ifconfig.me.",
#                     inputSchema=IPCheckOptions.model_json_schema(),
#                 )
#             ]
#
#         @server.list_prompts()
#         async def list_prompts() -> list[Prompt]:
#             logger.info("list_prompts called")
#             return [
#                 Prompt(
#                     name="ipcheck",
#                     description="Check the server's public IP address",
#                     arguments=[],
#                 )
#             ]
#
#         @server.call_tool()
#         async def call_tool(name, arguments: dict) -> list[TextContent]:
#             logger.info(f"call_tool called with name={name}, arguments={arguments}")
#
#             try:
#                 args = IPCheckOptions(**arguments)
#             except ValueError as e:
#                 error_msg = str(e)
#                 logger.error(f"Invalid parameters: {error_msg}")
#                 raise McpError(ErrorData(code=INVALID_PARAMS, message=error_msg))
#
#             format_type = args.format
#             if format_type not in ["text", "json"]:
#                 error_msg = "Format must be 'text' or 'json'"
#                 logger.error(error_msg)
#                 raise McpError(ErrorData(code=INVALID_PARAMS, message=error_msg))
#
#             ip_info = await get_ip_address(format_type, user_agent)
#
#             return [TextContent(
#                 type="text",
#                 text=f"Server IP information from ifconfig.me:\n{ip_info}"
#             )]
#
#         @server.get_prompt()
#         async def get_prompt(name: str, arguments: dict | None) -> GetPromptResult:
#             logger.info(f"get_prompt called with name={name}, arguments={arguments}")
#
#             try:
#                 ip_info = await get_ip_address("text", user_agent)
#             except McpError as e:
#                 logger.error(f"Error in get_prompt: {e}")
#                 return GetPromptResult(
#                     description="Failed to fetch IP address",
#                     messages=[
#                         PromptMessage(
#                             role="user",
#                             content=TextContent(type="text", text=str(e)),
#                         )
#                     ],
#                 )
#
#             return GetPromptResult(
#                 description="Server IP Address",
#                 messages=[
#                     PromptMessage(
#                         role="user",
#                         content=TextContent(type="text", text=f"The server's public IP address is: {ip_info}")
#                     )
#                 ],
#             )
#
#         options = server.create_initialization_options()
#         logger.info(f"Initialization options: {options}")
#
#         async with stdio_server() as (read_stream, write_stream):
#             logger.info("Starting server run loop")
#             await server.run(read_stream, write_stream, options, raise_exceptions=True)
#
#     except Exception as e:
#         logger.error(f"Unhandled exception: {e}", exc_info=True)
#         raise






async def serve(custom_user_agent: str | None = None, host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run the IP check MCP server."""
    try:
        server = Server("ipcheck_mcp")
        user_agent = custom_user_agent or DEFAULT_USER_AGENT

        logger.info(f"Starting MCP server with user agent: {user_agent}")
        logger.info(f"Starting MCP TCP server on {host}:{port} with user agent: {user_agent}")

        @server.list_tools()
        async def list_tools() -> list[Tool]:
            logger.info("list_tools called")
            return [
                Tool(
                    name="ipcheck",
                    description="Checks the server's public IP address by querying ifconfig.me.",
                    inputSchema=IPCheckOptions.model_json_schema(),
                )
            ]

        @server.list_prompts()
        async def list_prompts() -> list[Prompt]:
            logger.info("list_prompts called")
            return [
                Prompt(
                    name="ipcheck",
                    description="Check the server's public IP address",
                    arguments=[],
                )
            ]

        @server.call_tool()
        async def call_tool(name, arguments: dict) -> list[TextContent]:
            logger.info(f"call_tool called with name={name}, arguments={arguments}")

            try:
                args = IPCheckOptions(**arguments)
            except ValueError as e:
                error_msg = str(e)
                logger.error(f"Invalid parameters: {error_msg}")
                raise McpError(ErrorData(code=INVALID_PARAMS, message=error_msg))

            format_type = args.format
            if format_type not in ["text", "json"]:
                error_msg = "Format must be 'text' or 'json'"
                logger.error(error_msg)
                raise McpError(ErrorData(code=INVALID_PARAMS, message=error_msg))

            ip_info = await get_ip_address(format_type, user_agent)

            return [TextContent(
                type="text",
                text=f"Server IP information from ifconfig.me:\n{ip_info}"
            )]

        @server.get_prompt()
        async def get_prompt(name: str, arguments: dict | None) -> GetPromptResult:
            logger.info(f"get_prompt called with name={name}, arguments={arguments}")

            try:
                ip_info = await get_ip_address("text", user_agent)
            except McpError as e:
                logger.error(f"Error in get_prompt: {e}")
                return GetPromptResult(
                    description="Failed to fetch IP address",
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(type="text", text=str(e)),
                        )
                    ],
                )

            return GetPromptResult(
                description="Server IP Address",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(type="text", text=f"The server's public IP address is: {ip_info}")
                    )
                ],
            )

        options = server.create_initialization_options()
        logger.info(f"Initialization options: {options}")

        async with tcp_server(host, port) as (read_stream, write_stream):
            logger.info("Starting server run loop")
            await server.run(read_stream, write_stream, options, raise_exceptions=True)

    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    logger.info("Starting MCP server")
    logger.info(asyncio.run(get_ip_address("json")))
    try:
        asyncio.run(serve())
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
