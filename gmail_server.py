"""
Gmail MCP Server using FastMCP
Install: pip install mcp langchain-community google-auth google-auth-oauthlib google-api-python-client
"""

from mcp.server.fastmcp import FastMCP
from langchain_community.agent_toolkits import GmailToolkit
from langchain_community.tools.gmail.utils import build_resource_service, get_gmail_credentials
from typing import Optional

# Initialize FastMCP server
mcp = FastMCP("gmail")

# Global Gmail toolkit instance
_gmail_toolkit = None



def get_gmail_toolkit():
    """Initialize and return Gmail toolkit (singleton pattern)"""
    global _gmail_toolkit
    
    if _gmail_toolkit is None:
        credentials = get_gmail_credentials(
            token_file="token.json",
            scopes=["https://mail.google.com/"],
            client_secrets_file="credentials.json",
        )
        api_resource = build_resource_service(credentials=credentials)
        _gmail_toolkit = GmailToolkit(api_resource=api_resource)
    
    return _gmail_toolkit


@mcp.tool()
def search_gmail(query: str, max_results: int = 10) -> str:
    """
    Search Gmail messages using Gmail search syntax.
    
    Args:
        query: Gmail search query (e.g., 'from:example@gmail.com', 'is:unread', 'subject:meeting')
        max_results: Maximum number of results to return (default: 10)
    
    Returns:
        Search results as formatted string
    """
    toolkit = get_gmail_toolkit()
    tools = toolkit.get_tools()
    
    # Find search tool
    search_tool = next((t for t in tools if "search" in t.name.lower()), None)
    
    if search_tool:
        result = search_tool.invoke({"query": query, "max_results": max_results})
        return str(result)
    
    return "Search tool not found"


@mcp.tool()
def get_gmail_message(message_id: str) -> str:
    """
    Get the full content of a specific Gmail message by ID.
    
    Args:
        message_id: The unique Gmail message ID
    
    Returns:
        Full message content including headers, body, and metadata
    """
    toolkit = get_gmail_toolkit()
    tools = toolkit.get_tools()
    
    # Find get message tool
    get_tool = next((t for t in tools if "get" in t.name.lower() and "message" in t.name.lower()), None)
    
    if get_tool:
        result = get_tool.invoke({"message_id": message_id})
        return str(result)
    
    return "Get message tool not found"


@mcp.tool()
def send_gmail_message(to: str, subject: str, message: str, cc: Optional[str] = None, bcc: Optional[str] = None) -> str:
    """
    Send an email through Gmail.
    
    Args:
        to: Recipient email address (comma-separated for multiple)
        subject: Email subject line
        message: Email body content
        cc: CC recipients (optional, comma-separated)
        bcc: BCC recipients (optional, comma-separated)
    
    Returns:
        Confirmation message with sent email details
    """
    toolkit = get_gmail_toolkit()
    tools = toolkit.get_tools()
    
    # Find send tool
    send_tool = next((t for t in tools if "send" in t.name.lower()), None)
    
    if send_tool:
        params = {
            "to": to,
            "subject": subject,
            "message": message
        }
        if cc:
            params["cc"] = cc
        if bcc:
            params["bcc"] = bcc
            
        result = send_tool.invoke(params)
        return str(result)
    
    return "Send tool not found"


@mcp.tool()
def create_gmail_draft(to: str, subject: str, message: str) -> str:
    """
    Create a draft email in Gmail (not sent automatically).
    
    Args:
        to: Recipient email address
        subject: Email subject line
        message: Email body content
    
    Returns:
        Confirmation with draft ID
    """
    toolkit = get_gmail_toolkit()
    tools = toolkit.get_tools()
    
    # Find draft tool
    draft_tool = next((t for t in tools if "draft" in t.name.lower()), None)
    
    if draft_tool:
        result = draft_tool.invoke({
            "to": to,
            "subject": subject,
            "message": message
        })
        return str(result)
    
    return "Draft tool not found"


@mcp.tool()
def get_gmail_thread(thread_id: str) -> str:
    """
    Get an entire Gmail conversation thread by thread ID.
    
    Args:
        thread_id: The unique Gmail thread ID
    
    Returns:
        Complete thread with all messages in the conversation
    """
    toolkit = get_gmail_toolkit()
    tools = toolkit.get_tools()
    
    # Find thread tool
    thread_tool = next((t for t in tools if "thread" in t.name.lower()), None)
    
    if thread_tool:
        result = thread_tool.invoke({"thread_id": thread_id})
        return str(result)
    
    return "Thread tool not found"


if __name__ == "__main__":
    mcp.run(transport="stdio")