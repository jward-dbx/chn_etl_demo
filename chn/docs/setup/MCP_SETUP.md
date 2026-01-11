# 📋 PROMPT FOR CURSOR AGENT: DATABRICKS MCP SERVER SETUP

## OBJECTIVE
Configure Cursor to connect to Databricks Managed MCP servers for a new workspace. This will enable AI assistants in Cursor to directly query Databricks SQL, Genie spaces, Unity Catalog functions, and vector search indexes.

## BACKGROUND INFORMATION

### Current Reference Configuration
- **Current Workspace Host**: `https://your-workspace.cloud.databricks.com`
- **Current Databricks Token**: `dapi***REDACTED***`
- **Current Genie Space ID**: `01f0ed61506e1f7c9b993c728155babc` (Example Genie Space)
- **Current Catalog**: `your_catalog`
- **Current Schema**: `your_schema`

### Target Configuration (REPLACE THESE VALUES)
- **New Workspace Host**: `[PROVIDE_YOUR_WORKSPACE_URL]`
- **New Databricks Token**: `[PROVIDE_YOUR_NEW_TOKEN]`
- **New Genie Space ID**: `[OPTIONAL - IF APPLICABLE]`
- **New Catalog**: `[YOUR_CATALOG_NAME]`
- **New Schema**: `[YOUR_SCHEMA_NAME]`

---

## TASK: CREATE/UPDATE ~/.cursor/mcp.json

Create or update the file `~/.cursor/mcp.json` with the following configuration structure. This file configures 5 Databricks Managed MCP servers:

### Complete MCP Configuration Template

```json
{
  "mcpServers": {
    "databricks-dbsql": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-everything",
        "mcp-remote",
        "[YOUR_WORKSPACE_URL]/api/2.0/mcp/sql",
        "--header",
        "Authorization: Bearer [YOUR_DATABRICKS_TOKEN]"
      ]
    },
    "databricks-system-ai": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-everything",
        "mcp-remote",
        "[YOUR_WORKSPACE_URL]/api/2.0/mcp/functions/system/ai",
        "--header",
        "Authorization: Bearer [YOUR_DATABRICKS_TOKEN]"
      ]
    },
    "databricks-genie": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-everything",
        "mcp-remote",
        "[YOUR_WORKSPACE_URL]/api/2.0/mcp/genie/[YOUR_GENIE_SPACE_ID]",
        "--header",
        "Authorization: Bearer [YOUR_DATABRICKS_TOKEN]"
      ]
    },
    "databricks-uc-functions": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-everything",
        "mcp-remote",
        "[YOUR_WORKSPACE_URL]/api/2.0/mcp/functions/[YOUR_CATALOG]/[YOUR_SCHEMA]",
        "--header",
        "Authorization: Bearer [YOUR_DATABRICKS_TOKEN]"
      ]
    },
    "databricks-vector-search": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-everything",
        "mcp-remote",
        "[YOUR_WORKSPACE_URL]/api/2.0/mcp/vector-search/[YOUR_CATALOG]/[YOUR_SCHEMA]",
        "--header",
        "Authorization: Bearer [YOUR_DATABRICKS_TOKEN]"
      ]
    }
  }
}
```

---

## DETAILED REPLACEMENT INSTRUCTIONS

### 1. **databricks-dbsql** - SQL Query Execution
**Purpose**: Run AI-generated SQL queries on Databricks tables

Replace:
- `[YOUR_WORKSPACE_URL]` → Your Databricks workspace URL (e.g., `https://your-workspace.cloud.databricks.com`)
- `[YOUR_DATABRICKS_TOKEN]` → Your personal access token starting with `dapi...`

**Endpoint Pattern**: `/api/2.0/mcp/sql`

**Use Cases**:
- Execute SELECT queries on Unity Catalog tables
- Data pipeline authoring with AI
- Exploratory data analysis

---

### 2. **databricks-system-ai** - Python Interpreter & AI Functions
**Purpose**: Execute Python code and access built-in AI system functions

Replace:
- `[YOUR_WORKSPACE_URL]` → Your workspace URL
- `[YOUR_DATABRICKS_TOKEN]` → Your access token

**Endpoint Pattern**: `/api/2.0/mcp/functions/system/ai`

**Use Cases**:
- Run Python code in Databricks environment
- Access system-level AI functions
- Perform calculations and data transformations

---

### 3. **databricks-genie** - Natural Language Queries
**Purpose**: Query a specific Genie space using natural language

Replace:
- `[YOUR_WORKSPACE_URL]` → Your workspace URL
- `[YOUR_GENIE_SPACE_ID]` → The ID of your Genie space (find in Databricks UI under Genie Spaces)
- `[YOUR_DATABRICKS_TOKEN]` → Your access token

**Endpoint Pattern**: `/api/2.0/mcp/genie/{space_id}`

**How to Find Genie Space ID**:
1. Go to your Databricks workspace
2. Navigate to **Genie Spaces** (or **Agents** → **Genie**)
3. Click on your Genie space
4. The space ID is in the URL: `https://workspace.com/genie/{space_id}`

**Use Cases**:
- Ask natural language questions about your data
- Get insights without writing SQL
- Business user-friendly data access

**Note**: Skip this server if you don't have a Genie space deployed

---

### 4. **databricks-uc-functions** - Unity Catalog Functions
**Purpose**: Access SQL and Python functions in a specific Unity Catalog schema

Replace:
- `[YOUR_WORKSPACE_URL]` → Your workspace URL
- `[YOUR_CATALOG]` → Your Unity Catalog name (e.g., `main`, `dev`, `hls_glucosphere`)
- `[YOUR_SCHEMA]` → Your schema name (e.g., `default`, `cgm`, `analytics`)
- `[YOUR_DATABRICKS_TOKEN]` → Your access token

**Endpoint Pattern**: `/api/2.0/mcp/functions/{catalog}/{schema}`

**Use Cases**:
- Call custom Unity Catalog functions
- Execute predefined SQL queries
- Use registered Python UDFs

---

### 5. **databricks-vector-search** - Vector Search Indexes
**Purpose**: Query vector search indexes using semantic similarity

Replace:
- `[YOUR_WORKSPACE_URL]` → Your workspace URL
- `[YOUR_CATALOG]` → Your Unity Catalog name
- `[YOUR_SCHEMA]` → Your schema name (where vector indexes exist)
- `[YOUR_DATABRICKS_TOKEN]` → Your access token

**Endpoint Pattern**: `/api/2.0/mcp/vector-search/{catalog}/{schema}`

**Requirements**:
- Vector search index must exist in the specified catalog/schema
- Index must use Databricks-managed embeddings
- Vector search must be enabled on your workspace

**Use Cases**:
- Semantic document search
- Find similar records using vector embeddings
- RAG (Retrieval Augmented Generation) applications

**Note**: Skip this server if you don't have vector search indexes deployed

---

## STEP-BY-STEP SETUP PROCESS

### Step 1: Get Your Databricks Token
1. Navigate to your Databricks workspace
2. Click on your **profile icon** (top right)
3. Select **User Settings**
4. Go to **Developer** tab
5. Click **Access Tokens** → **Generate New Token**
6. Set expiration (recommend 90 days)
7. Copy the token (it starts with `dapi...`)
8. **IMPORTANT**: Save this token securely - you cannot view it again

### Step 2: Gather Required Information
Before configuring, collect:
- [ ] Workspace URL (e.g., `https://your-workspace.cloud.databricks.com`)
- [ ] Databricks Personal Access Token
- [ ] Catalog name (check Unity Catalog in Databricks UI)
- [ ] Schema name (check Unity Catalog in Databricks UI)
- [ ] Genie Space ID (optional - only if you have Genie spaces)
- [ ] Vector search indexes (optional - only if applicable)

### Step 3: Create/Edit the MCP Configuration File
```bash
# On Mac/Linux
nano ~/.cursor/mcp.json

# Or use VS Code
code ~/.cursor/mcp.json
```

### Step 4: Paste and Customize the Configuration
1. Copy the complete JSON template above
2. Replace all placeholders:
   - `[YOUR_WORKSPACE_URL]` → Your actual workspace URL (no trailing slash)
   - `[YOUR_DATABRICKS_TOKEN]` → Your `dapi...` token
   - `[YOUR_GENIE_SPACE_ID]` → Your Genie space ID (or remove this server block)
   - `[YOUR_CATALOG]` → Your catalog name
   - `[YOUR_SCHEMA]` → Your schema name

### Step 5: Set Secure File Permissions
```bash
chmod 600 ~/.cursor/mcp.json
```

### Step 6: Restart Cursor
**CRITICAL**: You must **fully quit** Cursor and reopen it (not just reload window)
- Mac: `Command + Q` then reopen
- Windows: Close all windows then reopen
- Linux: Quit application then reopen

### Step 7: Verify Connection
After restart, open Cursor's AI chat and test:

```
"List all available MCP tools from Databricks"
```

Expected result: You should see tools from the configured MCP servers

---

## EXAMPLE: COMPLETED CONFIGURATION

Here's what the config looks like with actual values filled in (based on the current workspace):

```json
{
  "mcpServers": {
    "databricks-dbsql": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-everything",
        "mcp-remote",
        "https://your-workspace.cloud.databricks.com/api/2.0/mcp/sql",
        "--header",
        "Authorization: Bearer dapi***REDACTED***"
      ]
    },
    "databricks-system-ai": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-everything",
        "mcp-remote",
        "https://your-workspace.cloud.databricks.com/api/2.0/mcp/functions/system/ai",
        "--header",
        "Authorization: Bearer dapi***REDACTED***"
      ]
    },
    "databricks-genie": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-everything",
        "mcp-remote",
        "https://your-workspace.cloud.databricks.com/api/2.0/mcp/genie/01f0ed61506e1f7c9b993c728155babc",
        "--header",
        "Authorization: Bearer dapi***REDACTED***"
      ]
    },
    "databricks-uc-functions": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-everything",
        "mcp-remote",
        "https://your-workspace.cloud.databricks.com/api/2.0/mcp/functions/your_catalog/your_schema",
        "--header",
        "Authorization: Bearer dapi***REDACTED***"
      ]
    },
    "databricks-vector-search": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-everything",
        "mcp-remote",
        "https://your-workspace.cloud.databricks.com/api/2.0/mcp/vector-search/your_catalog/your_schema",
        "--header",
        "Authorization: Bearer dapi***REDACTED***"
      ]
    }
  }
}
```

---

## TESTING & VALIDATION

### Test Each MCP Server

#### 1. Test DBSQL (Primary)
```
"Write a SQL query to list the top 10 tables in the [YOUR_CATALOG] catalog"
```

#### 2. Test System AI
```
"Use Python to calculate the factorial of 20"
```

#### 3. Test Genie
```
"Query the Genie space: What tables are available?"
```

#### 4. Test UC Functions
```
"List all Unity Catalog functions in [YOUR_CATALOG].[YOUR_SCHEMA]"
```

#### 5. Test Vector Search
```
"Show me vector search indexes in [YOUR_CATALOG].[YOUR_SCHEMA]"
```

---

## TROUBLESHOOTING

### Issue: "MCP servers not loading"
**Solution**:
1. Verify `~/.cursor/mcp.json` file exists
2. Check file has correct permissions: `ls -la ~/.cursor/mcp.json`
3. Ensure JSON is valid (use a JSON validator)
4. Fully quit and restart Cursor (not just reload)
5. Check Cursor console: `View` → `Toggle Developer Tools` → `Console`

### Issue: "401 Unauthorized"
**Solution**:
1. Token expired - generate new token in Databricks
2. Token incorrect - verify you copied it correctly
3. Update token in `~/.cursor/mcp.json`
4. Restart Cursor

### Issue: "404 Not Found"
**Solution**:
1. Verify workspace URL is correct (no typos)
2. Check Genie space ID exists
3. Confirm catalog and schema names are correct
4. Ensure MCP is enabled on your workspace

### Issue: "Connection timeout"
**Solution**:
1. Check network connectivity
2. Verify IP access lists in Databricks (if configured)
3. Check firewall/VPN settings
4. Ensure workspace is accessible from your location

---

## SECURITY BEST PRACTICES

### Token Security
- ⚠️ **NEVER** commit `~/.cursor/mcp.json` to git
- ⚠️ **NEVER** share your token with others
- ⚠️ **ROTATE** tokens every 90 days
- ⚠️ Use **workspace-specific** tokens (don't reuse)
- ⚠️ Set **appropriate expiration** dates

### File Permissions
```bash
# Ensure only you can read the file
chmod 600 ~/.cursor/mcp.json

# Verify permissions
ls -la ~/.cursor/mcp.json
# Expected: -rw------- (600)
```

### Token Scope
- Use tokens with **minimum required permissions**
- Consider using **service principals** for production
- Use **OAuth** for team-based access (see advanced options)

---

## ADVANCED: OPTIONAL CONFIGURATIONS

### Using Multiple Workspaces
You can configure multiple Databricks workspaces by adding more server entries:

```json
{
  "mcpServers": {
    "databricks-prod-sql": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-everything",
        "mcp-remote",
        "https://prod-workspace.cloud.databricks.com/api/2.0/mcp/sql",
        "--header",
        "Authorization: Bearer dapi_prod_token_here"
      ]
    },
    "databricks-dev-sql": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-everything",
        "mcp-remote",
        "https://dev-workspace.cloud.databricks.com/api/2.0/mcp/sql",
        "--header",
        "Authorization: Bearer dapi_dev_token_here"
      ]
    }
  }
}
```

### Using Environment Variables (More Secure)
1. Set environment variable:
```bash
export DATABRICKS_TOKEN="dapi..."
```

2. Use in config:
```json
{
  "mcpServers": {
    "databricks-dbsql": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-everything",
        "mcp-remote",
        "https://your-workspace.cloud.databricks.com/api/2.0/mcp/sql",
        "--header",
        "Authorization: Bearer $DATABRICKS_TOKEN"
      ],
      "env": {
        "DATABRICKS_TOKEN": "${DATABRICKS_TOKEN}"
      }
    }
  }
}
```

---

## SUMMARY OF 5 MCP SERVERS

| Server Name | Endpoint Pattern | Purpose | Required Info |
|-------------|------------------|---------|---------------|
| **databricks-dbsql** | `/api/2.0/mcp/sql` | Run SQL queries | Workspace URL, Token |
| **databricks-system-ai** | `/api/2.0/mcp/functions/system/ai` | Python interpreter & AI functions | Workspace URL, Token |
| **databricks-genie** | `/api/2.0/mcp/genie/{space_id}` | Natural language queries | Workspace URL, Token, Genie Space ID |
| **databricks-uc-functions** | `/api/2.0/mcp/functions/{catalog}/{schema}` | Unity Catalog functions | Workspace URL, Token, Catalog, Schema |
| **databricks-vector-search** | `/api/2.0/mcp/vector-search/{catalog}/{schema}` | Vector similarity search | Workspace URL, Token, Catalog, Schema |

---

## REFERENCES

- [Databricks MCP Documentation](https://docs.databricks.com/aws/en/generative-ai/mcp/managed-mcp)
- [Available Managed Servers](https://docs.databricks.com/aws/en/generative-ai/mcp/managed-mcp#available-managed-servers)
- [Connect External Clients](https://docs.databricks.com/aws/en/generative-ai/mcp/connect-external-services)
- [Model Context Protocol Spec](https://modelcontextprotocol.io/)
- [Cursor MCP Documentation](https://docs.cursor.com/mcp)

---

## ✅ CHECKLIST

Before considering setup complete:

- [ ] Generated Databricks Personal Access Token
- [ ] Collected workspace URL, catalog, and schema names
- [ ] Created/updated `~/.cursor/mcp.json` with all 5 servers
- [ ] Replaced all placeholder values with actual values
- [ ] Set file permissions to 600
- [ ] Fully quit and restarted Cursor
- [ ] Tested connection with sample queries
- [ ] Verified tools are available in Cursor AI
- [ ] Documented token for future rotation

---

**END OF SETUP PROMPT**

This prompt contains everything needed to configure Cursor MCP servers for a new Databricks workspace. Simply provide your workspace-specific values and follow the steps!
