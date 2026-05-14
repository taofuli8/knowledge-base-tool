import httpx
import trafilatura
from typing import Optional


async def fetch_web_content(url: str, max_length: int = 50000) -> dict:
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; KnowledgeBaseBot/1.0)"
                }
            )
            response.raise_for_status()
    except httpx.TimeoutException:
        return {"success": False, "error": "Request timed out"}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"HTTP error: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": f"Failed to fetch: {str(e)}"}

    content = trafilatura.extract(response.text, include_comments=False, include_tables=True)
    if not content:
        content = response.text

    truncated = len(content) > max_length
    if truncated:
        content = content[:max_length]

    return {
        "success": True,
        "content": content,
        "truncated": truncated,
        "url": url,
    }


async def fetch_github_readme(repo_url: str) -> dict:
    repo_url = repo_url.rstrip("/")
    parts = repo_url.split("github.com/")
    if len(parts) < 2:
        return {"success": False, "error": "Invalid GitHub URL"}

    owner_repo = parts[1]
    api_url = f"https://api.github.com/repos/{owner_repo}/readme"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(api_url, headers={"Accept": "application/vnd.github.v3+json"})

            if response.status_code == 404:
                return {"success": False, "error": "README not found"}
            response.raise_for_status()

            data = response.json()
            import base64
            readme_content = base64.b64decode(data["content"]).decode("utf-8")
            return {
                "success": True,
                "content": readme_content,
                "repo": owner_repo,
            }
    except httpx.TimeoutException:
        return {"success": False, "error": "GitHub API request timed out"}
    except Exception as e:
        return {"success": False, "error": f"Failed to fetch GitHub README: {str(e)}"}


async def fetch_github_info(repo_url: str) -> dict:
    repo_url = repo_url.rstrip("/")
    parts = repo_url.split("github.com/")
    if len(parts) < 2:
        return {"success": False, "error": "Invalid GitHub URL"}

    owner_repo = parts[1]
    api_url = f"https://api.github.com/repos/{owner_repo}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(api_url, headers={"Accept": "application/vnd.github.v3+json"})
            response.raise_for_status()
            data = response.json()
            return {
                "success": True,
                "title": data.get("name", owner_repo),
                "description": data.get("description", ""),
                "url": data.get("html_url", repo_url),
                "language": data.get("language", ""),
                "stars": data.get("stargazers_count", 0),
            }
    except Exception as e:
        return {"success": False, "error": f"Failed to fetch GitHub info: {str(e)}"}
