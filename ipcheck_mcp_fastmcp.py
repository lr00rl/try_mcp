import logging
import sys
import asyncio
import httpx
# 使用 Literal 来更精确地定义可选参数
from typing import Literal

# 从 SDK 文档看，FastMCP 在 mcp.server.fastmcp
from mcp.server.fastmcp import FastMCP
# 如果 prompt 需要返回结构化消息，可以导入
# from mcp.server.fastmcp.prompts import base

# --- 日志记录设置 (保持不变，可以改个日志文件名区分) ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='mcp_server_fastmcp.log', # 新日志文件
    filemode='w'
)
logger = logging.getLogger("/home/cdcd/roobli/JustCoding/try_mcp/ipcheck_fastmcp") # 新 logger 名称

# --- User Agent (作为模块级常量) ---
DEFAULT_USER_AGENT = "ModelContextProtocol/1.0 (IP Checker via FastMCP)"

# --- 核心 IP 获取逻辑 (不变) ---
async def get_ip_address(format_type: str = "text", user_agent: str = DEFAULT_USER_AGENT) -> str:
    """Fetch the server's public IP address from ifconfig.me"""
    url = "https://ifconfig.me"
    if format_type == "json":
        url += "/all.json"
    elif format_type != "text":
        raise ValueError("Invalid format_type specified.")

    logger.info(f"Fetching IP from {url}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                follow_redirects=True,
                headers={"User-Agent": user_agent},
                timeout=10,
            )
            response.raise_for_status()
            logger.info("Successfully fetched IP address")
            return response.text
    except httpx.HTTPError as e:
        error_msg = f"Failed to fetch IP address: {e!r}"
        logger.error(error_msg)
        raise RuntimeError(f"HTTP Error fetching IP: {response.status_code}") from e
    except Exception as e:
        error_msg = f"An unexpected error occurred: {e!r}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError("Unexpected error fetching IP") from e


# --- 创建 FastMCP 服务器实例 ---
mcp_server = FastMCP("IPCheckServer")

# --- 定义工具 ---
# 移除 mcp_server.state.user_agent = DEFAULT_USER_AGENT 这一行
@mcp_server.tool()
async def ipcheck(format: Literal["text", "json"] = "text") -> str:
    """
    Checks the server's public IP address using ifconfig.me.
    Allows specifying the output format.

    Args:
        format: The desired output format ('text' or 'json'). Defaults to 'text'.
    """
    logger.info(f"Tool 'ipcheck' called with format='{format}'")
    # 直接使用模块级常量 DEFAULT_USER_AGENT
    user_agent = DEFAULT_USER_AGENT
    try:
        ip_info = await get_ip_address(format_type=format, user_agent=user_agent)
        return f"Server IP information ({format}):\n{ip_info}"
    except Exception as e:
        logger.error(f"Error executing ipcheck tool: {e}", exc_info=True)
        raise

# --- 定义提示 (可选，作为示例) ---
@mcp_server.prompt()
async def show_ip() -> str:
    """
    Gets and displays the server's public IP address (text format).
    """
    logger.info("Prompt 'show_ip' called")
    # 直接使用模块级常量 DEFAULT_USER_AGENT
    user_agent = DEFAULT_USER_AGENT
    try:
        ip_info = await get_ip_address(format_type="text", user_agent=user_agent)
        return f"The server's public IP address is: {ip_info}"
    except Exception as e:
        logger.error(f"Error executing show_ip prompt: {e}", exc_info=True)
        return f"Sorry, I encountered an error trying to fetch the IP address: {str(e)}"

# --- 运行服务器 ---
if __name__ == "__main__":
    logger.info(f"Starting {mcp_server.name} using FastMCP...")
    try:
        mcp_server.run(transport='stdio')
    except Exception as e:
        logger.critical(f"Fatal error running FastMCP server: {e}", exc_info=True)
        sys.exit(1)
