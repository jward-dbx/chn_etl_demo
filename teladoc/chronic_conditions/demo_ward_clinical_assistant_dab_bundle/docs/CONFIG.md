# Configuration Guide

This guide explains how to configure your Databricks workspace URL and authentication token.

## Quick Start

1. **Copy the template file**:
   ```bash
   cp .env.local.template .env.local
   ```

2. **Edit `.env.local`** with your values:
   ```bash
   # Open in your editor
   nano .env.local
   # or
   code .env.local
   ```

3. **Fill in your values**:
   ```bash
   DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
   DATABRICKS_TOKEN=YOUR-PERSONAL-ACCESS-TOKEN-HERE
   DATABRICKS_USERNAME=your.email@databricks.com
   ```

4. **Run the setup script** (it will automatically use `.env.local`):
   ```bash
   ./scripts/setup_config.sh
   ```

## Configuration File: `.env.local`

The `.env.local` file is a simple key-value file where you store your credentials:

```bash
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-personal-access-token
DATABRICKS_USERNAME=your.email@databricks.com
```

### Why `.env.local`?

- ✅ **Gitignored**: Your credentials are never committed to git
- ✅ **Simple**: Easy to edit with any text editor
- ✅ **Automatic**: The setup script automatically reads from it
- ✅ **Secure**: Only exists on your local machine

## How It Works

1. **Create `.env.local`** from the template:
   ```bash
   cp .env.local.template .env.local
   ```

2. **Edit `.env.local`** with your actual values

3. **Run the setup script**:
   ```bash
   ./scripts/setup_config.sh
   ```
   
   The script will:
   - Automatically load values from `.env.local`
   - Configure the Databricks CLI
   - Update `.env.local` if you provide new values via prompts

## Getting Your Values

### Workspace URL (`DATABRICKS_HOST`)

Your workspace URL is in the format:
```
https://YOUR-WORKSPACE.cloud.databricks.com
```

You can find it:
- In your browser when logged into Databricks
- In your Databricks account settings
- From your Databricks admin

### Personal Access Token (`DATABRICKS_TOKEN`)

1. Log into your Databricks workspace
2. Click your username in the top right
3. Go to **User Settings** → **Access Tokens**
4. Click **Generate New Token**
5. Give it a name (e.g., "Bundle Deployment")
6. Set expiration (or leave blank for no expiration)
7. Click **Generate**
8. **Copy the token immediately** (you won't see it again!)

### Username (`DATABRICKS_USERNAME`)

Your Databricks username/email address. This is used to construct the workspace path where files will be stored.

## Example `.env.local` File

```bash
# Databricks Configuration
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=YOUR-PERSONAL-ACCESS-TOKEN-HERE
DATABRICKS_USERNAME=your.email@databricks.com
```

## Security Best Practices

1. ✅ **Never commit `.env.local`** - It's already in `.gitignore`
2. ✅ **Use least-privilege tokens** - Only grant necessary permissions
3. ✅ **Rotate tokens regularly** - Update `.env.local` when you rotate
4. ✅ **Don't share `.env.local`** - Each person should have their own
5. ✅ **Use different tokens** - One for development, one for production

## Troubleshooting

### Script doesn't find `.env.local`

Make sure:
- The file is named exactly `.env.local` (with the dot at the start)
- The file is in the root directory (or same directory as `scripts/setup_config.sh`)
- The file has read permissions: `chmod 600 .env.local`

### Values not being used

The script uses this priority order:
1. Command-line arguments (`--workspace-url`, `--token`)
2. `.env.local` file
3. Environment variables
4. Interactive prompts

If you want to override `.env.local`, use command-line arguments:
```bash
./scripts/setup_config.sh --workspace-url "https://other-workspace.cloud.databricks.com"
```

### File permissions

For security, set restrictive permissions on `.env.local`:
```bash
chmod 600 .env.local
```

This ensures only you can read/write the file.

## Alternative: Manual Configuration

If you prefer not to use `.env.local`, you can:

1. **Use command-line arguments**:
   ```bash
   ./scripts/setup_config.sh --workspace-url URL --token TOKEN --username USERNAME
   ```

2. **Use environment variables**:
   ```bash
   export DATABRICKS_HOST="https://workspace.cloud.databricks.com"
   export DATABRICKS_TOKEN="your-token"
   ./setup_config.sh
   ```

3. **Use Databricks CLI directly**:
   ```bash
   databricks configure --token
   ```

