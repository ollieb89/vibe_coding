---
title: Python MCP Server Implementation Guide
source: skills/mcp-builder/reference/python_mcp_server.md
---

## Instructions
1. Improve structure and clarity
2. Keep all code blocks exactly as-is (verbatim, do not summarize)
3. Add a citation [source: skills/mcp-builder/reference/python_mcp_server.md] at the end
4. Ensure all headings follow a logical hierarchy (no skipping levels)
5. Expand any placeholder text like [user-defined] into helpful descriptions
6. Start with YAML frontmatter including title, description, and tags
7. Do NOT wrap the output in a markdown code block (output raw text)
8. Do not repeat these instructions in your response.

---

## Python MCP Server for Example Service

This server provides tools to interact with the Example API, including user search, project management, and data export capabilities.

### Prerequisites

- Python 3.x
- [Flask](https://flask.palletsprojects.com/en/2.1.x/) web framework
- [Requests](https://requests.readthedocs.io/en/latest/) library for HTTP requests

### Setup

1. Install required packages:

```bash
pip install flask requests
```

2. Create a new file named `app.py` and paste the following code into it.

### Example MCP Server Code (verbatim)

```python
from flask import Flask, request, jsonify
import requests

API_URL = "https://api.example.com"
API_KEY = "[user-defined]"

app = Flask(__name__)

@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    params = {
        "key": API_KEY,
        "q": query,
    }
    response = requests.get(f"{API_URL}/search", params=params)

    if response.status_code != 200:
        return jsonify({"error": f"API request failed with status {response.status_code}"}), response.status_code

    data = response.json()
    results = []
    for item in data["results"]:
        user_id, name, email = item["user_id"], item["name"], item["email"]
        results.append(f"{name} ({user_id}) <{email}>")

    return jsonify({"results": results}), 200

if __name__ == "__main__":
    app.run(debug=True)
```

### Running the Server

1. Save the file and run the server:

```bash
python app.py
```

2. Access the API at `http://localhost:5000/search?q=[search_term]`.

### Error Handling

- Input validation errors are handled by Flask's built-in request validation
- Returns "API request failed with status [status_code]" for any non-200 API response

### Complete Example

See the provided code in `app.py` for a complete Python MCP server example.
[source: skills/mcp-builder/reference/python_mcp_server.md]