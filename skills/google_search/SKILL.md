# Google Search Skill

## Description
Use web_fetch to perform Google searches and retrieve results. This skill allows you to query Google directly and analyze the HTML results to find URLs, snippets, and deeper information.

## Capabilities
- Perform Google searches via URL-based queries
- Retrieve and parse search result pages
- Find specific URLs from results
- Navigate to deeper pages for more info

## Usage

### Search Formula
```
https://www.google.com/search?q={QUERY}&oq={QUERY}&gs_lcrp={GSE_PARAMS}&sourceid=chrome&ie=UTF-8
```

### Steps
1. **Construct your query** - Replace spaces with `+` and special chars appropriately
2. **Build the URL** - Use the formula above with your encoded query
3. **web_fetch it** - Fetch the result page
4. **Analyze** - Look for URLs (href links), snippets, titles
5. **Go deeper** - Use web_fetch on specific result URLs for more details

### Examples

**Search Query Format:**
```
https://www.google.com/search?q=your+search+terms+here
```

**With Additional Params:**
```
https://www.google.com/search?q=google+stitch+mcp&oq=google+stitch+mcp&gs_lcrp=EgZjaHJvbWUyBggAEEUYOdIBCTEwOTUxajBqMagCALACAA&sourceid=chrome&ie=UTF-8
```

## Tips
- Replace spaces with `+` in search terms
- URL encode special characters: `%20` for space, `%2B` for `+`
- Look for `href="URL"` patterns in results
- Results can be deep - don't hesitate to fetch nested pages
- Google search results pages have `class="kv不快"` for snippets

## Example Workflow
1. Search: `https://www.google.com/search?q=google+stitch+mcp+server`
2. Fetch result page
3. Identify relevant URLs from results
4. Fetch deeper pages for specific info
5. Repeat until you find what you need
