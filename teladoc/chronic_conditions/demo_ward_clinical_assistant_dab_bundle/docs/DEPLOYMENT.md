# Deployment Guide

This guide explains how to configure and deploy the Clinical Assistant Databricks Asset Bundle.

## Prerequisites

1. **Databricks CLI** installed and configured
2. **Personal Access Token (PAT)** with appropriate permissions
3. **Workspace access** with permissions for:
   - Unity Catalog (create catalog/schema/volume)
   - SQL Warehouse access
   - Workspace file storage
   - Apps deployment
   - Jobs creation

## Quick Setup

### Option 1: Interactive Setup Script (Recommended)

Run the setup script to configure everything:

```bash
./scripts/setup_config.sh
```

This will:
- Prompt for your workspace URL
- Prompt for your Personal Access Token
- Configure the Databricks CLI
- Create a `config/config.local` file with your settings

### Option 2: Manual Configuration

#### Step 1: Configure Databricks CLI

Configure the Databricks CLI with your workspace credentials:

```bash
databricks configure --token
```

You'll be prompted for:
- **Workspace URL**: `https://your-workspace.cloud.databricks.com`
- **Token**: Your Personal Access Token

This creates/updates `~/.databrickscfg` with your credentials.

#### Step 2: Create Local Configuration (Optional)

Copy the template and fill in your values:

```bash
cp config/config.template config/config.local
```

Edit `config/config.local` with your settings:
- `DATABRICKS_HOST`: Your workspace URL
- `DATABRICKS_TOKEN`: Your Personal Access Token (optional if using CLI config)
- `WORKSPACE_PATH`: Where files will be synced in workspace
- `CATALOG`: Unity Catalog catalog name
- `SCHEMA`: Unity Catalog schema name

**Note**: `config/config.local` is gitignored and won't be committed.

#### Step 3: Update Bundle Variables (Optional)

Edit `databricks.yml` to update default variables if needed:

```yaml
variables:
  workspace_path:
    default: /Users/YOUR-USERNAME@databricks.com/demo_ward_clinical_assistant
  catalog:
    default: your-catalog-name
  schema:
    default: your-schema-name
```

Or override at deployment time:

```bash
databricks bundle deploy -v workspace_path=/Users/your.email@databricks.com/demo_ward_clinical_assistant
```

## Deployment

### Validate Configuration

Before deploying, validate your bundle configuration:

```bash
databricks bundle validate
```

### Deploy the Bundle

Deploy all resources to your workspace:

```bash
databricks bundle deploy
```

This will:
1. Create Unity Catalog resources (catalog, schema, volume)
2. Upload files to workspace
3. Deploy jobs, dashboards, and apps
4. Set up agent bricks (Genie, Knowledge Assistant, Multi-Agent Supervisor)

### Run the Workflow

After deployment, run the data generation workflow:

```bash
databricks bundle run demo_workflow
```

Or trigger it from the Databricks UI:
- Go to **Workflows** → **Jobs**
- Find the job: `[DEMOGEN] - demo_ward_clinical_assistant - Data Generation and Transformation`
- Click **Run now**

## Authentication Methods

### Method 1: Databricks CLI Config (Recommended)

The Databricks CLI uses `~/.databrickscfg` for authentication. This is the standard method and works automatically with bundle deployments.

**File location**: `~/.databrickscfg`

**Format**:
```ini
[DEFAULT]
host = https://your-workspace.cloud.databricks.com
token = your-personal-access-token
```

### Method 2: Environment Variables

You can also set environment variables:

```bash
export DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
export DATABRICKS_TOKEN=your-personal-access-token
```

### Method 3: Bundle Variables

For workspace-specific settings, use bundle variables in `databricks.yml` or override at deployment:

```bash
databricks bundle deploy -v workspace_path=/path/to/workspace
```

## Configuration Files

| File | Purpose | Git Tracked? |
|------|---------|--------------|
| `~/.databrickscfg` | Databricks CLI authentication | ❌ No (user home) |
| `config/config.local` | Local workspace configuration | ❌ No (gitignored) |
| `config/config.template` | Configuration template | ✅ Yes |
| `.databrickscfg.template` | CLI config template | ✅ Yes |
| `databricks.yml` | Bundle configuration | ✅ Yes |

## Troubleshooting

### Authentication Errors

If you get authentication errors:

1. **Check CLI config**:
   ```bash
   cat ~/.databrickscfg
   ```

2. **Reconfigure CLI**:
   ```bash
   databricks configure --token
   ```

3. **Test connection**:
   ```bash
   databricks clusters list
   ```

### Workspace Path Issues

If deployment fails due to workspace path:

1. Check your username in the workspace path
2. Ensure the path exists or you have permission to create it
3. Update `workspace_path` variable in `databricks.yml`

### Missing Permissions

If you get permission errors:

1. Verify your PAT has required permissions:
   - `workspace:write` - For file uploads
   - `catalogs:write` - For Unity Catalog resources
   - `jobs:write` - For job creation
   - `apps:write` - For app deployment

2. Check workspace admin settings for Unity Catalog access

## Next Steps

After successful deployment:

1. **Access the App**: Go to **Apps** in Databricks UI and open "Clinical Assistant"
2. **View Dashboard**: Go to **Dashboards** and open "Chronic Care Ops & Risk Monitoring"
3. **Check Agent Bricks**: Go to **Agent Bricks** to see Genie, KA, and MAS resources
4. **Run Jobs**: Monitor the data generation workflow in **Workflows**

## Security Notes

- ⚠️ **Never commit** `~/.databrickscfg` or `config/config.local` to git
- ⚠️ **Never commit** Personal Access Tokens
- ✅ Use `.gitignore` to exclude sensitive files
- ✅ Rotate tokens regularly
- ✅ Use least-privilege permissions for PATs

