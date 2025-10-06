from mcp.server.fastmcp import FastMCP
import requests
import os
import base64
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

mcp = FastMCP("github")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN environment variable is required")

BASE_URL = "https://api.github.com"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "MCP-GitHub-Server"
}

def api_request(method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
    """Helper function for GitHub API requests"""
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.request(method, url, headers=HEADERS, json=data, params=params)
        response.raise_for_status()
        return response.json() if response.content else {"success": True}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

@mcp.tool()
def create_or_update_file(owner: str, repo: str, path: str, content: str, message: str, branch: str, sha: Optional[str] = None) -> Dict[str, Any]:
    """Create or update a single file in a repository"""
    encoded_content = base64.b64encode(content.encode()).decode()
    data = {"message": message, "content": encoded_content, "branch": branch}
    if sha:
        data["sha"] = sha
    return api_request("PUT", f"/repos/{owner}/{repo}/contents/{path}", data)

@mcp.tool()
def push_files(owner: str, repo: str, branch: str, files: List[Dict[str, str]], message: str) -> Dict[str, Any]:
    """Push multiple files in a single commit"""
    ref_response = api_request("GET", f"/repos/{owner}/{repo}/git/ref/heads/{branch}")
    if "error" in ref_response:
        return ref_response
    
    base_sha = ref_response["object"]["sha"]
    commit_response = api_request("GET", f"/repos/{owner}/{repo}/git/commits/{base_sha}")
    if "error" in commit_response:
        return commit_response
    
    tree_sha = commit_response["tree"]["sha"]
    tree_items = []
    
    for file in files:
        blob_data = {"content": file["content"], "encoding": "utf-8"}
        blob_response = api_request("POST", f"/repos/{owner}/{repo}/git/blobs", blob_data)
        if "error" in blob_response:
            return blob_response
        tree_items.append({"path": file["path"], "mode": "100644", "type": "blob", "sha": blob_response["sha"]})
    
    new_tree = api_request("POST", f"/repos/{owner}/{repo}/git/trees", {"base_tree": tree_sha, "tree": tree_items})
    if "error" in new_tree:
        return new_tree
    
    new_commit = api_request("POST", f"/repos/{owner}/{repo}/git/commits", {"message": message, "tree": new_tree["sha"], "parents": [base_sha]})
    if "error" in new_commit:
        return new_commit
    
    return api_request("PATCH", f"/repos/{owner}/{repo}/git/refs/heads/{branch}", {"sha": new_commit["sha"]})

@mcp.tool()
def search_repositories(query: str, page: Optional[int] = 1, perPage: Optional[int] = 30) -> Dict[str, Any]:
    """Search for GitHub repositories"""
    params = {"q": query, "page": page, "per_page": min(perPage, 100)}
    return api_request("GET", "/search/repositories", params=params)

@mcp.tool()
def create_repository(name: str, description: Optional[str] = None, private: Optional[bool] = False, autoInit: Optional[bool] = False) -> Dict[str, Any]:
    """Create a new GitHub repository"""
    data = {"name": name, "private": private, "auto_init": autoInit}
    if description:
        data["description"] = description
    return api_request("POST", "/user/repos", data)

@mcp.tool()
def get_file_contents(owner: str, repo: str, path: str, branch: Optional[str] = None) -> Dict[str, Any]:
    """Get contents of a file or directory"""
    params = {"ref": branch} if branch else {}
    response = api_request("GET", f"/repos/{owner}/{repo}/contents/{path}", params=params)
    if "content" in response and "encoding" in response:
        if response["encoding"] == "base64":
            response["decoded_content"] = base64.b64decode(response["content"]).decode('utf-8')
    return response

@mcp.tool()
def create_issue(owner: str, repo: str, title: str, body: Optional[str] = None, assignees: Optional[List[str]] = None, labels: Optional[List[str]] = None, milestone: Optional[int] = None) -> Dict[str, Any]:
    """Create a new issue"""
    data = {"title": title}
    if body:
        data["body"] = body
    if assignees:
        data["assignees"] = assignees
    if labels:
        data["labels"] = labels
    if milestone:
        data["milestone"] = milestone
    return api_request("POST", f"/repos/{owner}/{repo}/issues", data)

@mcp.tool()
def create_pull_request(owner: str, repo: str, title: str, head: str, base: str, body: Optional[str] = None, draft: Optional[bool] = False, maintainer_can_modify: Optional[bool] = True) -> Dict[str, Any]:
    """Create a new pull request"""
    data = {"title": title, "head": head, "base": base, "draft": draft, "maintainer_can_modify": maintainer_can_modify}
    if body:
        data["body"] = body
    return api_request("POST", f"/repos/{owner}/{repo}/pulls", data)

@mcp.tool()
def fork_repository(owner: str, repo: str, organization: Optional[str] = None) -> Dict[str, Any]:
    """Fork a repository"""
    data = {"organization": organization} if organization else {}
    return api_request("POST", f"/repos/{owner}/{repo}/forks", data)

@mcp.tool()
def create_branch(owner: str, repo: str, branch: str, from_branch: Optional[str] = None) -> Dict[str, Any]:
    """Create a new branch"""
    if from_branch:
        ref_response = api_request("GET", f"/repos/{owner}/{repo}/git/ref/heads/{from_branch}")
    else:
        repo_response = api_request("GET", f"/repos/{owner}/{repo}")
        if "error" in repo_response:
            return repo_response
        ref_response = api_request("GET", f"/repos/{owner}/{repo}/git/ref/heads/{repo_response['default_branch']}")
    
    if "error" in ref_response:
        return ref_response
    
    sha = ref_response["object"]["sha"]
    return api_request("POST", f"/repos/{owner}/{repo}/git/refs", {"ref": f"refs/heads/{branch}", "sha": sha})

@mcp.tool()
def list_issues(owner: str, repo: str, state: Optional[str] = "open", labels: Optional[List[str]] = None, sort: Optional[str] = "created", direction: Optional[str] = "desc", since: Optional[str] = None, page: Optional[int] = 1, per_page: Optional[int] = 30) -> List[Dict[str, Any]]:
    """List and filter repository issues"""
    params = {"state": state, "sort": sort, "direction": direction, "page": page, "per_page": min(per_page, 100)}
    if labels:
        params["labels"] = ",".join(labels)
    if since:
        params["since"] = since
    return api_request("GET", f"/repos/{owner}/{repo}/issues", params=params)

@mcp.tool()
def update_issue(owner: str, repo: str, issue_number: int, title: Optional[str] = None, body: Optional[str] = None, state: Optional[str] = None, labels: Optional[List[str]] = None, assignees: Optional[List[str]] = None, milestone: Optional[int] = None) -> Dict[str, Any]:
    """Update an existing issue"""
    data = {}
    if title:
        data["title"] = title
    if body:
        data["body"] = body
    if state:
        data["state"] = state
    if labels:
        data["labels"] = labels
    if assignees:
        data["assignees"] = assignees
    if milestone:
        data["milestone"] = milestone
    return api_request("PATCH", f"/repos/{owner}/{repo}/issues/{issue_number}", data)

@mcp.tool()
def add_issue_comment(owner: str, repo: str, issue_number: int, body: str) -> Dict[str, Any]:
    """Add a comment to an issue"""
    return api_request("POST", f"/repos/{owner}/{repo}/issues/{issue_number}/comments", {"body": body})

@mcp.tool()
def search_code(q: str, sort: Optional[str] = None, order: Optional[str] = "desc", per_page: Optional[int] = 30, page: Optional[int] = 1) -> Dict[str, Any]:
    """Search for code across GitHub repositories"""
    params = {"q": q, "per_page": min(per_page, 100), "page": page, "order": order}
    if sort:
        params["sort"] = sort
    return api_request("GET", "/search/code", params=params)

@mcp.tool()
def search_issues(q: str, sort: Optional[str] = None, order: Optional[str] = "desc", per_page: Optional[int] = 30, page: Optional[int] = 1) -> Dict[str, Any]:
    """Search for issues and pull requests"""
    params = {"q": q, "per_page": min(per_page, 100), "page": page, "order": order}
    if sort:
        params["sort"] = sort
    return api_request("GET", "/search/issues", params=params)

@mcp.tool()
def search_users(q: str, sort: Optional[str] = None, order: Optional[str] = "desc", per_page: Optional[int] = 30, page: Optional[int] = 1) -> Dict[str, Any]:
    """Search for GitHub users"""
    params = {"q": q, "per_page": min(per_page, 100), "page": page, "order": order}
    if sort:
        params["sort"] = sort
    return api_request("GET", "/search/users", params=params)

@mcp.tool()
def list_commits(owner: str, repo: str, page: Optional[int] = 1, per_page: Optional[int] = 30, sha: Optional[str] = None) -> List[Dict[str, Any]]:
    """Gets commits of a branch in a repository"""
    params = {"page": page, "per_page": min(per_page, 100)}
    if sha:
        params["sha"] = sha
    return api_request("GET", f"/repos/{owner}/{repo}/commits", params=params)

@mcp.tool()
def get_issue(owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
    """Gets the contents of an issue within a repository"""
    return api_request("GET", f"/repos/{owner}/{repo}/issues/{issue_number}")

@mcp.tool()
def get_pull_request(owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
    """Get details of a specific pull request"""
    return api_request("GET", f"/repos/{owner}/{repo}/pulls/{pull_number}")

@mcp.tool()
def list_pull_requests(owner: str, repo: str, state: Optional[str] = "open", head: Optional[str] = None, base: Optional[str] = None, sort: Optional[str] = "created", direction: Optional[str] = "desc", per_page: Optional[int] = 30, page: Optional[int] = 1) -> List[Dict[str, Any]]:
    """List and filter repository pull requests"""
    params = {"state": state, "sort": sort, "direction": direction, "per_page": min(per_page, 100), "page": page}
    if head:
        params["head"] = head
    if base:
        params["base"] = base
    return api_request("GET", f"/repos/{owner}/{repo}/pulls", params=params)

@mcp.tool()
def create_pull_request_review(owner: str, repo: str, pull_number: int, body: str, event: str, commit_id: Optional[str] = None, comments: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Create a review on a pull request"""
    data = {"body": body, "event": event}
    if commit_id:
        data["commit_id"] = commit_id
    if comments:
        data["comments"] = comments
    return api_request("POST", f"/repos/{owner}/{repo}/pulls/{pull_number}/reviews", data)

@mcp.tool()
def merge_pull_request(owner: str, repo: str, pull_number: int, commit_title: Optional[str] = None, commit_message: Optional[str] = None, merge_method: Optional[str] = "merge") -> Dict[str, Any]:
    """Merge a pull request"""
    data = {"merge_method": merge_method}
    if commit_title:
        data["commit_title"] = commit_title
    if commit_message:
        data["commit_message"] = commit_message
    return api_request("PUT", f"/repos/{owner}/{repo}/pulls/{pull_number}/merge", data)

@mcp.tool()
def get_pull_request_files(owner: str, repo: str, pull_number: int) -> List[Dict[str, Any]]:
    """Get the list of files changed in a pull request"""
    return api_request("GET", f"/repos/{owner}/{repo}/pulls/{pull_number}/files")

@mcp.tool()
def get_pull_request_status(owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
    """Get the combined status of all status checks for a pull request"""
    pr_response = api_request("GET", f"/repos/{owner}/{repo}/pulls/{pull_number}")
    if "error" in pr_response:
        return pr_response
    return api_request("GET", f"/repos/{owner}/{repo}/commits/{pr_response['head']['sha']}/status")

@mcp.tool()
def update_pull_request_branch(owner: str, repo: str, pull_number: int, expected_head_sha: Optional[str] = None) -> Dict[str, Any]:
    """Update a pull request branch with the latest changes from the base branch"""
    data = {}
    if expected_head_sha:
        data["expected_head_sha"] = expected_head_sha
    return api_request("PUT", f"/repos/{owner}/{repo}/pulls/{pull_number}/update-branch", data)

@mcp.tool()
def get_pull_request_comments(owner: str, repo: str, pull_number: int) -> List[Dict[str, Any]]:
    """Get the review comments on a pull request"""
    return api_request("GET", f"/repos/{owner}/{repo}/pulls/{pull_number}/comments")

@mcp.tool()
def get_pull_request_reviews(owner: str, repo: str, pull_number: int) -> List[Dict[str, Any]]:
    """Get the reviews on a pull request"""
    return api_request("GET", f"/repos/{owner}/{repo}/pulls/{pull_number}/reviews")

if __name__ == "__main__":
    mcp.run(transport="stdio")