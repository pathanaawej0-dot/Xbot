---
name: notion
description: "Notion API operations. Use when: (1) creating database items, (2) fetching page content, (3) updating tasks or logs."
metadata:
  openclaw:
    requires:
      bins: []
---

# Notion Skill

Interact with Notion databases and pages using the Notion API.

## Requirements
Requires a `NOTION_TOKEN` in `.env`.

## Common API Endpoints

- **Search**: `https://api.notion.com/v1/search`
- **Create Page**: `https://api.notion.com/v1/pages`
- **Retrieve Database**: `https://api.notion.com/v1/databases/{database_id}`

## Usage Example (Python/Requests)

```python
import requests

headers = {
    "Authorization": f"Bearer {os.getenv('NOTION_TOKEN')}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# Fetching a database
response = requests.post("https://api.notion.com/v1/search", headers=headers, json={"query": "your query"})
```

## Best Practices
- **JSON Structure**: Always verify the Notion JSON schema (properties vs content).
- **Rate Limits**: Notion has strict rate limits; do not spam requests in a loop.
