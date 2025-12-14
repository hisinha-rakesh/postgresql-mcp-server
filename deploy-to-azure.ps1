###############################################################################
# PostgreSQL Docker to Azure Container Instance Deployment Script (PowerShell)
# This script automates the deployment of PostgreSQL to Azure
###############################################################################

###############################################################################
# Load Configuration from .env.deployment file
###############################################################################

if (!(Test-Path ".env.deployment")) {
    Write-Host "✗ .env.deployment file not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please create .env.deployment file with your configuration:" -ForegroundColor Yellow
    Write-Host "  Copy-Item .env.deployment.example .env.deployment"
    Write-Host "  # Edit .env.deployment with your values"
    exit 1
}

# Load environment variables from .env.deployment
Get-Content ".env.deployment" | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        Set-Variable -Name $name -Value $value -Scope Script
    }
}

# Configuration Variables (from .env.deployment)
$ACR_NAME = "${ACR_NAME_PREFIX}$(Get-Date -Format 'yyyyMMddHHmmss')"
$DNS_NAME_LABEL = "${DNS_NAME_PREFIX}-$(Get-Date -Format 'yyyyMMddHHmmss')"

# Database Configuration (from .env.deployment)
$DB_NAME = $POSTGRES_DB
$DB_USER = $POSTGRES_USER
$DB_PASSWORD = $POSTGRES_PASSWORD

###############################################################################
# Functions
###############################################################################

function Write-Header {
    param($Message)
    Write-Host "`n========================================" -ForegroundColor Blue
    Write-Host $Message -ForegroundColor Blue
    Write-Host "========================================`n" -ForegroundColor Blue
}

function Write-Success {
    param($Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param($Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Info {
    param($Message)
    Write-Host "→ $Message" -ForegroundColor Yellow
}

function Check-Prerequisites {
    Write-Header "Checking Prerequisites"

    # Check Docker
    if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error-Custom "Docker is not installed. Please install Docker Desktop first."
        exit 1
    }
    $dockerVersion = docker --version
    Write-Success "Docker is installed: $dockerVersion"

    # Check Azure CLI
    if (!(Get-Command az -ErrorAction SilentlyContinue)) {
        Write-Error-Custom "Azure CLI is not installed. Please install Azure CLI first."
        exit 1
    }
    $azVersion = az --version | Select-Object -First 1
    Write-Success "Azure CLI is installed: $azVersion"

    # Check if logged in to Azure
    try {
        az account show | Out-Null
        Write-Success "Logged in to Azure"
    } catch {
        Write-Error-Custom "Not logged in to Azure. Please run 'az login' first."
        exit 1
    }

    # Check if Dockerfile exists
    if (!(Test-Path "Dockerfile")) {
        Write-Error-Custom "Dockerfile not found in current directory"
        exit 1
    }
    Write-Success "Dockerfile found"

    # Check if .env.deployment exists
    if (!(Test-Path ".env.deployment")) {
        Write-Error-Custom ".env.deployment file not found"
        Write-Host ""
        Write-Host "Please create .env.deployment file:" -ForegroundColor Yellow
        Write-Host "  Copy-Item .env.deployment.example .env.deployment"
        Write-Host "  # Edit .env.deployment with your values"
        exit 1
    }
    Write-Success ".env.deployment found"

    # Validate password is not default
    if ($DB_PASSWORD -eq "CHANGE_THIS_PASSWORD_BEFORE_DEPLOYMENT") {
        Write-Error-Custom "Please change the default password in .env.deployment!"
        exit 1
    }
    Write-Success "Configuration validated"
}

function Create-ResourceGroup {
    Write-Header "Creating Resource Group"

    $exists = az group exists --name $RESOURCE_GROUP
    if ($exists -eq "true") {
        Write-Info "Resource group '$RESOURCE_GROUP' already exists"
    } else {
        Write-Info "Creating resource group '$RESOURCE_GROUP' in '$LOCATION'..."
        az group create --name $RESOURCE_GROUP --location $LOCATION --output none
        Write-Success "Resource group created"
    }
}

function Create-ContainerRegistry {
    Write-Header "Creating Azure Container Registry"

    # Check if ACR exists
    $acrExists = az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP 2>$null
    if ($acrExists) {
        Write-Info "ACR '$ACR_NAME' already exists"
    } else {
        Write-Info "Creating Azure Container Registry '$ACR_NAME'..."
        az acr create `
            --resource-group $RESOURCE_GROUP `
            --name $ACR_NAME `
            --sku Basic `
            --admin-enabled true `
            --output none
        Write-Success "ACR created"
    }

    # Login to ACR
    Write-Info "Logging in to ACR..."
    az acr login --name $ACR_NAME
    Write-Success "Logged in to ACR"
}

function Build-AndPushImage {
    Write-Header "Building and Pushing Docker Image"

    $fullImageName = "$ACR_NAME.azurecr.io/${IMAGE_NAME}:${IMAGE_TAG}"

    # Build the image
    Write-Info "Building Docker image..."
    docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .
    Write-Success "Docker image built"

    # Tag for ACR
    Write-Info "Tagging image for ACR..."
    docker tag "${IMAGE_NAME}:${IMAGE_TAG}" $fullImageName
    Write-Success "Image tagged"

    # Push to ACR
    Write-Info "Pushing image to ACR (this may take a few minutes)..."
    docker push $fullImageName
    Write-Success "Image pushed to ACR"

    Write-Host "Full image name: $fullImageName" -ForegroundColor Green
}

function Deploy-ContainerInstance {
    Write-Header "Deploying Azure Container Instance"

    $fullImageName = "$ACR_NAME.azurecr.io/${IMAGE_NAME}:${IMAGE_TAG}"

    # Get ACR credentials
    Write-Info "Retrieving ACR credentials..."
    $acrUsername = az acr credential show --name $ACR_NAME --query username --output tsv
    $acrPassword = az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv

    # Delete existing container if it exists
    $containerExists = az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME 2>$null
    if ($containerExists) {
        Write-Info "Deleting existing container instance..."
        az container delete `
            --resource-group $RESOURCE_GROUP `
            --name $CONTAINER_NAME `
            --yes `
            --output none
        Write-Success "Existing container deleted"
    }

    # Create new container instance
    Write-Info "Creating container instance (this may take 2-3 minutes)..."
    az container create `
        --resource-group $RESOURCE_GROUP `
        --name $CONTAINER_NAME `
        --image $fullImageName `
        --cpu $CPU_CORES `
        --memory $MEMORY_GB `
        --registry-login-server "${ACR_NAME}.azurecr.io" `
        --registry-username $acrUsername `
        --registry-password $acrPassword `
        --ports 5432 `
        --dns-name-label $DNS_NAME_LABEL `
        --ip-address Public `
        --environment-variables `
            POSTGRES_DB=$DB_NAME `
            POSTGRES_USER=$DB_USER `
            POSTGRES_PASSWORD=$DB_PASSWORD `
        --output none

    Write-Success "Container instance created"
}

function Get-ConnectionInfo {
    Write-Header "Connection Information"

    # Get public IP
    $publicIp = az container show `
        --resource-group $RESOURCE_GROUP `
        --name $CONTAINER_NAME `
        --query ipAddress.ip `
        --output tsv

    # Get FQDN
    $fqdn = az container show `
        --resource-group $RESOURCE_GROUP `
        --name $CONTAINER_NAME `
        --query ipAddress.fqdn `
        --output tsv

    Write-Host "`nDeployment Complete!" -ForegroundColor Green
    Write-Host "`nConnection Details:" -ForegroundColor Yellow
    Write-Host "  Public IP:    " -NoNewline; Write-Host $publicIp -ForegroundColor Green
    Write-Host "  FQDN:         " -NoNewline; Write-Host $fqdn -ForegroundColor Green
    Write-Host "  Port:         " -NoNewline; Write-Host "5432" -ForegroundColor Green
    Write-Host "  Database:     " -NoNewline; Write-Host $DB_NAME -ForegroundColor Green
    Write-Host "  Username:     " -NoNewline; Write-Host $DB_USER -ForegroundColor Green
    Write-Host "  Password:     " -NoNewline; Write-Host $DB_PASSWORD -ForegroundColor Green

    Write-Host "`nConnection String:" -ForegroundColor Yellow
    Write-Host "postgresql://$DB_USER:$DB_PASSWORD@${publicIp}:5432/$DB_NAME" -ForegroundColor Green

    Write-Host "`nMCP Configuration (.mcp.json):" -ForegroundColor Yellow
    $mcpConfig = @"
{
  "mcpServers": {
    "postgres-enterprise": {
      "command": "C:\\Users\\kusha\\postgresql-mcp\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\kusha\\postgresql-mcp\\mcp_server_enterprise.py"],
      "env": {
        "DATABASE_URL": "postgresql://$DB_USER:$DB_PASSWORD@${publicIp}:5432/$DB_NAME"
      }
    }
  }
}
"@
    Write-Host $mcpConfig -ForegroundColor Blue

    # Save to file
    $deploymentInfo = @"
PostgreSQL Azure Container Instance - Deployment Information
=============================================================

Deployment Date: $(Get-Date)

Connection Details:
-------------------
Public IP:    $publicIp
FQDN:         $fqdn
Port:         5432
Database:     $DB_NAME
Username:     $DB_USER
Password:     $DB_PASSWORD

Connection String:
------------------
postgresql://$DB_USER:$DB_PASSWORD@${publicIp}:5432/$DB_NAME

psql Command:
-------------
psql "postgresql://$DB_USER:$DB_PASSWORD@${publicIp}:5432/$DB_NAME"

Azure Resources:
----------------
Resource Group: $RESOURCE_GROUP
ACR Name:       $ACR_NAME
ACI Name:       $CONTAINER_NAME
Location:       $LOCATION

MCP Configuration:
------------------
Update your .mcp.json with:
$mcpConfig
"@

    $deploymentInfo | Out-File -FilePath "deployment-info.txt" -Encoding UTF8
    Write-Success "Connection information saved to 'deployment-info.txt'"
}

function Test-Connection {
    Write-Header "Testing Connection"

    $publicIp = az container show `
        --resource-group $RESOURCE_GROUP `
        --name $CONTAINER_NAME `
        --query ipAddress.ip `
        --output tsv

    Write-Info "Waiting for PostgreSQL to be ready (may take 30-60 seconds)..."
    Start-Sleep -Seconds 30

    if (Get-Command psql -ErrorAction SilentlyContinue) {
        Write-Info "Testing connection with psql..."
        $env:PGPASSWORD = $DB_PASSWORD
        $result = psql -h $publicIp -U $DB_USER -d $DB_NAME -c "SELECT version();" 2>$null
        if ($?) {
            Write-Success "Connection test successful!"
        } else {
            Write-Error-Custom "Connection test failed. Container may still be starting. Try again in a minute."
        }
        Remove-Item Env:\PGPASSWORD
    } else {
        Write-Info "psql not installed. Skipping connection test."
    }
}

function Show-CleanupInfo {
    Write-Header "Cleanup (Optional)"
    Write-Host "`nTo delete all resources created by this script, run:" -ForegroundColor Yellow
    Write-Host "az group delete --name $RESOURCE_GROUP --yes --no-wait" -ForegroundColor Red
}

###############################################################################
# Main Execution
###############################################################################

function Main {
    Clear-Host
    Write-Host @"
╔═══════════════════════════════════════════════════════════╗
║   PostgreSQL Azure Container Instance Deployment         ║
║   Automated Deployment Script (PowerShell)               ║
╚═══════════════════════════════════════════════════════════╝
"@ -ForegroundColor Blue

    # Run all steps
    Check-Prerequisites
    Create-ResourceGroup
    Create-ContainerRegistry
    Build-AndPushImage
    Deploy-ContainerInstance
    Get-ConnectionInfo
    Test-Connection
    Show-CleanupInfo

    Write-Host "`n"
    Write-Success "Deployment completed successfully!"
    Write-Host ""
}

# Run main function
Main
