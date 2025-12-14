# PostgreSQL Azure Container Instance - Deployment Guide

This guide explains how to deploy PostgreSQL to Azure Container Instance using the automated deployment scripts.

## 📋 Prerequisites

Before running the deployment script, ensure you have:

1. **Docker Desktop** installed and running
   - Download: https://www.docker.com/products/docker-desktop

2. **Azure CLI** installed
   - Windows: https://aka.ms/installazurecliwindows
   - Mac: `brew install azure-cli`
   - Linux: https://docs.microsoft.com/cli/azure/install-azure-cli-linux

3. **Azure Account** with active subscription
   - Sign up: https://azure.microsoft.com/free/

4. **Logged in to Azure**
   ```bash
   az login
   ```

5. **PostgreSQL Client Tools** (optional, for testing)
   - Already installed at: `C:\Program Files\PostgreSQL\18\bin\psql.exe`

---

## 🚀 Quick Start

### Option 1: Using Bash Script (Git Bash on Windows, or Linux/Mac)

```bash
# Navigate to the project directory
cd C:/Users/kusha/postgresql-mcp

# Make script executable (Linux/Mac only)
chmod +x deploy-to-azure.sh

# Run the deployment
./deploy-to-azure.sh
```

### Option 2: Using PowerShell Script (Windows)

```powershell
# Navigate to the project directory
cd C:\Users\kusha\postgresql-mcp

# Allow script execution (first time only)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run the deployment
.\deploy-to-azure.ps1
```

---

## 📝 What the Script Does

The automated deployment script performs the following steps:

### 1. Prerequisites Check
- ✓ Verifies Docker is installed
- ✓ Verifies Azure CLI is installed
- ✓ Checks Azure login status
- ✓ Confirms Dockerfile exists

### 2. Resource Group Creation
- Creates Azure Resource Group: `rg-postgres-mcp`
- Location: `eastus` (configurable in script)

### 3. Azure Container Registry (ACR) Setup
- Creates ACR with unique name: `acrpostgresmcp<timestamp>`
- Enables admin access
- Logs in to the registry

### 4. Docker Image Build & Push
- Builds PostgreSQL 17 Docker image from Dockerfile
- Tags image for ACR
- Pushes image to Azure Container Registry

### 5. Azure Container Instance (ACI) Deployment
- Creates container instance: `aci-postgres-library`
- Configures with:
  - 1 CPU core
  - 1.5 GB memory
  - Public IP address
  - Unique DNS name
  - Environment variables for PostgreSQL

### 6. Connection Information
- Retrieves public IP address
- Displays connection string
- Generates MCP configuration
- Saves all info to `deployment-info.txt`

### 7. Connection Test
- Waits for PostgreSQL to start (30 seconds)
- Tests connection with `psql` (if available)

---

## 🔧 Configuration

You can customize the deployment by editing variables at the top of the script:

### Bash Script (`deploy-to-azure.sh`)
```bash
RESOURCE_GROUP="rg-postgres-mcp"
LOCATION="eastus"
ACR_NAME="acrpostgresmcp$(date +%s)"
IMAGE_NAME="postgres-library"
CONTAINER_NAME="aci-postgres-library"

# Database Configuration
DB_NAME="librarydatabase"
DB_USER="rakuser"
DB_PASSWORD="rakpassword"

# Container Resources
CPU_CORES="1"
MEMORY_GB="1.5"
```

### PowerShell Script (`deploy-to-azure.ps1`)
```powershell
$RESOURCE_GROUP = "rg-postgres-mcp"
$LOCATION = "eastus"
$DB_NAME = "librarydatabase"
$DB_USER = "rakuser"
$DB_PASSWORD = "rakpassword"
```

---

## 📊 Expected Output

The script will display:

```
╔═══════════════════════════════════════════════════════════╗
║   PostgreSQL Azure Container Instance Deployment         ║
║   Automated Deployment Script                            ║
╚═══════════════════════════════════════════════════════════╝

========================================
Checking Prerequisites
========================================
✓ Docker is installed: Docker version 24.0.6
✓ Azure CLI is installed: azure-cli 2.54.0
✓ Logged in to Azure
✓ Dockerfile found

========================================
Creating Resource Group
========================================
→ Creating resource group 'rg-postgres-mcp' in 'eastus'...
✓ Resource group created

========================================
Creating Azure Container Registry
========================================
→ Creating Azure Container Registry 'acrpostgresmcp1702123456'...
✓ ACR created
→ Logging in to ACR...
✓ Logged in to ACR

========================================
Building and Pushing Docker Image
========================================
→ Building Docker image...
✓ Docker image built
→ Tagging image for ACR...
✓ Image tagged
→ Pushing image to ACR (this may take a few minutes)...
✓ Image pushed to ACR

========================================
Deploying Azure Container Instance
========================================
→ Creating container instance (this may take 2-3 minutes)...
✓ Container instance created

========================================
Connection Information
========================================

Deployment Complete!

Connection Details:
  Public IP:    20.232.77.76
  FQDN:         postgres-mcp-db-1702123456.eastus.azurecontainer.io
  Port:         5432
  Database:     librarydatabase
  Username:     rakuser
  Password:     rakpassword

Connection String:
postgresql://rakuser:rakpassword@20.232.77.76:5432/librarydatabase

✓ Connection information saved to 'deployment-info.txt'

✓ Deployment completed successfully!
```

---

## 🔌 Update MCP Configuration

After deployment, update your `.mcp.json` file with the new connection string:

```json
{
  "mcpServers": {
    "postgres-enterprise": {
      "command": "C:\\Users\\kusha\\postgresql-mcp\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\kusha\\postgresql-mcp\\mcp_server_enterprise.py"],
      "env": {
        "DATABASE_URL": "postgresql://rakuser:rakpassword@20.232.77.76:5432/librarydatabase"
      }
    }
  }
}
```

**Location:** `C:\Users\kusha\.mcp.json`

---

## 🧪 Testing the Deployment

### Test 1: Direct PostgreSQL Connection

```bash
# Using psql
psql "postgresql://rakuser:rakpassword@20.232.77.76:5432/librarydatabase"

# Or with environment variable
$env:PGPASSWORD="rakpassword"
psql -h 20.232.77.76 -U rakuser -d librarydatabase
```

### Test 2: Python Connection Test

```bash
cd C:\Users\kusha\postgresql-mcp
python test_azure_connection.py
```

### Test 3: MCP Server Test

```bash
# Restart Claude Code to load new configuration
# Then in Claude Code:
# Ask: "Show me all tables in my database"
```

---

## 🗑️ Cleanup / Delete Resources

To delete all Azure resources created by the script:

```bash
# Delete entire resource group
az group delete --name rg-postgres-mcp --yes --no-wait

# Or individually:
az container delete --resource-group rg-postgres-mcp --name aci-postgres-library --yes
az acr delete --resource-group rg-postgres-mcp --name acrpostgresmcp1702123456 --yes
az group delete --name rg-postgres-mcp --yes
```

---

## ⚠️ Troubleshooting

### Issue 1: "Docker command not found"
**Solution:**
- Install Docker Desktop: https://www.docker.com/products/docker-desktop
- Ensure Docker is running (check system tray)

### Issue 2: "az command not found"
**Solution:**
- Install Azure CLI: https://docs.microsoft.com/cli/azure/install-azure-cli
- Restart terminal after installation

### Issue 3: "Not logged in to Azure"
**Solution:**
```bash
az login
# Follow browser authentication
```

### Issue 4: "ACR name already exists"
**Solution:**
- The script uses timestamps to create unique names
- If issue persists, manually change `ACR_NAME` in the script

### Issue 5: "Connection test failed"
**Possible causes:**
- PostgreSQL container is still starting (wait 1-2 minutes)
- Firewall blocking port 5432
- Check container logs:
  ```bash
  az container logs --resource-group rg-postgres-mcp --name aci-postgres-library
  ```

### Issue 6: "Container creation failed"
**Solution:**
```bash
# Check container status
az container show --resource-group rg-postgres-mcp --name aci-postgres-library

# View container logs
az container logs --resource-group rg-postgres-mcp --name aci-postgres-library

# Delete and retry
az container delete --resource-group rg-postgres-mcp --name aci-postgres-library --yes
# Re-run deployment script
```

---

## 💰 Azure Costs

**Estimated Monthly Cost (as of 2024):**

- **Azure Container Instance:**
  - 1 vCPU: ~$30/month
  - 1.5 GB Memory: ~$5/month
  - **Total ACI:** ~$35/month

- **Azure Container Registry (Basic):**
  - Storage: ~$5/month
  - **Total ACR:** ~$5/month

**Total Estimated Cost: ~$40/month**

**Cost Optimization Tips:**
1. Stop container when not in use:
   ```bash
   az container stop --resource-group rg-postgres-mcp --name aci-postgres-library
   ```
2. Use Azure Free Tier credits (first 30 days)
3. Delete resources when not needed

---

## 🔒 Security Recommendations

1. **Change Default Password**
   - Edit `DB_PASSWORD` in script before deployment
   - Use strong passwords (16+ characters, mixed case, numbers, symbols)

2. **Restrict Network Access**
   - Add firewall rules to limit IP addresses
   - Use Azure Virtual Network for private access

3. **Enable SSL/TLS**
   - PostgreSQL in container should enforce SSL
   - Add `?sslmode=require` to connection string

4. **Use Azure Key Vault**
   - Store DATABASE_URL in Key Vault
   - Reference in MCP configuration

5. **Regular Backups**
   - Use MCP server's backup tools
   - Schedule automated backups

6. **Monitor Access**
   - Enable Azure Monitor
   - Set up alerts for suspicious activity

---

## 📚 Additional Resources

- **Azure Container Instances:** https://docs.microsoft.com/azure/container-instances/
- **Azure Container Registry:** https://docs.microsoft.com/azure/container-registry/
- **PostgreSQL Docker Image:** https://hub.docker.com/_/postgres
- **MCP Server Documentation:** `MCP_README.md`
- **Setup Guide:** `SETUP_GUIDE.md`

---

## 🆘 Support

If you encounter issues:

1. Check `deployment-info.txt` for connection details
2. Review container logs: `az container logs --resource-group rg-postgres-mcp --name aci-postgres-library`
3. Test connection with `psql` directly
4. Verify MCP server configuration in `.mcp.json`
5. Check Claude Code logs: `~/.claude/debug/`

---

## ✅ Deployment Checklist

- [ ] Docker Desktop installed and running
- [ ] Azure CLI installed
- [ ] Logged in to Azure (`az login`)
- [ ] Dockerfile exists in project directory
- [ ] Customized configuration variables (password, etc.)
- [ ] Run deployment script
- [ ] Wait for completion (5-10 minutes)
- [ ] Save `deployment-info.txt`
- [ ] Update `.mcp.json` with new connection string
- [ ] Restart Claude Code
- [ ] Test database connection
- [ ] Test MCP server functionality

---

**Deployment Date:** $(Get-Date)
**Script Version:** 1.0
**Last Updated:** December 2024
