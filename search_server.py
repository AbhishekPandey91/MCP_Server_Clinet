from mcp.server.fastmcp import FastMCP
import requests
import sys
import json

# Create MCP server instance
mcp = FastMCP("search_tools")

# ---------------- DuckDuckGo ----------------
@mcp.tool()
def DuckDuckGoSearchRun(query: str) -> str:
    """
    Performs privacy-focused web searches using DuckDuckGo's API.
    Returns a formatted string of search results with title, URL, and snippet.
    """
    try:
        url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        results = []
        
        # Check AbstractText first (most relevant result)
        if data.get("AbstractText"):
            results.append(f"📌 {data.get('Heading', 'Result')}\n{data['AbstractText']}\n🔗 {data.get('AbstractURL', 'N/A')}\n")
        
        # Add related topics
        for topic in data.get("RelatedTopics", [])[:5]:  # Limit to 5 results
            if "Text" in topic and "FirstURL" in topic:
                results.append(f"• {topic['Text'][:200]}...\n🔗 {topic['FirstURL']}\n")
        
        if not results:
            return f"No results found for '{query}'. Try a different search term."
        
        return "\n".join(results)
    
    except Exception as e:
        return f"Error searching DuckDuckGo: {str(e)}"


# ---------------- Wikipedia ----------------
@mcp.tool()
def WikipediaQueryRun(query: str, sentences: int = 5) -> str:
    """
    Searches Wikipedia for a query and returns summary and URL.
    Returns formatted string with title, summary, and URL.
    """
    try:
        import wikipedia
        
        # Set language to English
        wikipedia.set_lang("en")
        
        # Search and get summary
        summary = wikipedia.summary(query, sentences=sentences, auto_suggest=True)
        page = wikipedia.page(query, auto_suggest=True)
        
        result = f"📖 Wikipedia: {page.title}\n\n{summary}\n\n🔗 Read more: {page.url}"
        return result
    
    except wikipedia.exceptions.DisambiguationError as e:
        # Handle disambiguation - return options
        options = ', '.join(e.options[:5])
        return f"⚠️ Multiple results found for '{query}'. Please be more specific. Options: {options}"
    
    except wikipedia.exceptions.PageError:
        return f"❌ No Wikipedia page found for '{query}'. Try a different search term."
    
    except Exception as e:
        return f"Error searching Wikipedia: {str(e)}"


# ---------------- Web Search (Alternative) ----------------
@mcp.tool()
def web_search(query: str) -> str:
    """
    General web search that tries Wikipedia first, then DuckDuckGo.
    Best for general queries.
    """
    # Try Wikipedia first
    wiki_result = WikipediaQueryRun(query, sentences=3)
    if not wiki_result.startswith("Error") and not wiki_result.startswith("❌"):
        return wiki_result
    
    # Fall back to DuckDuckGo
    return DuckDuckGoSearchRun(query)


# ---------------- Run MCP Server ----------------
if __name__ == "__main__":
    try:
        # Log to stderr so it doesn't interfere with MCP protocol
        print("🔧 Search Tools MCP Server starting...", file=sys.stderr)
        mcp.run(transport="stdio")
    except Exception as e:
        print(f"❌ Server error: {e}", file=sys.stderr)
        sys.exit(1)