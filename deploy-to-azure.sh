#!/bin/bash
###############################################################################
# PostgreSQL Docker to Azure Container Instance Deployment Script
# This script automates the deployment of PostgreSQL to Azure
###############################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

###############################################################################
# Load Configuration from .env.deployment file
###############################################################################

if [ ! -f ".env.deployment" ]; then
    print_error ".env.deployment file not found!"
    echo ""
    echo "Please create .env.deployment file with your configuration:"
    echo "  cp .env.deployment.example .env.deployment"
    echo "  # Edit .env.deployment with your values"
    exit 1
fi

# Load environment variables from .env.deployment
export $(grep -v '^#' .env.deployment | xargs)

# Configuration Variables (from .env.deployment)
ACR_NAME="${ACR_NAME_PREFIX}$(date +%s)"  # Unique name with timestamp
DNS_NAME_LABEL="${DNS_NAME_PREFIX}-$(date +%s)"  # Unique DNS name

# Database Configuration (from .env.deployment)
DB_NAME="${POSTGRES_DB}"
DB_USER="${POSTGRES_USER}"
DB_PASSWORD="${POSTGRES_PASSWORD}"

###############################################################################
# Functions
###############################################################################

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    print_success "Docker is installed: $(docker --version)"

    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed. Please install Azure CLI first."
        exit 1
    fi
    print_success "Azure CLI is installed: $(az --version | head -n 1)"

    # Check if logged in to Azure
    if ! az account show &> /dev/null; then
        print_error "Not logged in to Azure. Please run 'az login' first."
        exit 1
    fi
    print_success "Logged in to Azure"

    # Check if Dockerfile exists
    if [ ! -f "Dockerfile" ]; then
        print_error "Dockerfile not found in current directory"
        exit 1
    fi
    print_success "Dockerfile found"

    # Check if .env.deployment exists
    if [ ! -f ".env.deployment" ]; then
        print_error ".env.deployment file not found"
        echo ""
        echo "Please create .env.deployment file:"
        echo "  cp .env.deployment.example .env.deployment"
        echo "  # Edit .env.deployment with your values"
        exit 1
    fi
    print_success ".env.deployment found"

    # Validate password is not default
    if [ "$DB_PASSWORD" == "CHANGE_THIS_PASSWORD_BEFORE_DEPLOYMENT" ]; then
        print_error "Please change the default password in .env.deployment!"
        exit 1
    fi
    print_success "Configuration validated"
}

create_resource_group() {
    print_header "Creating Resource Group"

    if az group exists --name "$RESOURCE_GROUP" | grep -q "true"; then
        print_info "Resource group '$RESOURCE_GROUP' already exists"
    else
        print_info "Creating resource group '$RESOURCE_GROUP' in '$LOCATION'..."
        az group create \
            --name "$RESOURCE_GROUP" \
            --location "$LOCATION" \
            --output none
        print_success "Resource group created"
    fi
}

create_container_registry() {
    print_header "Creating Azure Container Registry"

    # Check if ACR exists
    if az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        print_info "ACR '$ACR_NAME' already exists"
    else
        print_info "Creating Azure Container Registry '$ACR_NAME'..."
        az acr create \
            --resource-group "$RESOURCE_GROUP" \
            --name "$ACR_NAME" \
            --sku Basic \
            --admin-enabled true \
            --output none
        print_success "ACR created"
    fi

    # Login to ACR
    print_info "Logging in to ACR..."
    az acr login --name "$ACR_NAME"
    print_success "Logged in to ACR"
}

build_and_push_image() {
    print_header "Building and Pushing Docker Image"

    local full_image_name="${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${IMAGE_TAG}"

    # Build the image
    print_info "Building Docker image..."
    docker build -t "$IMAGE_NAME:$IMAGE_TAG" .
    print_success "Docker image built"

    # Tag for ACR
    print_info "Tagging image for ACR..."
    docker tag "$IMAGE_NAME:$IMAGE_TAG" "$full_image_name"
    print_success "Image tagged"

    # Push to ACR
    print_info "Pushing image to ACR (this may take a few minutes)..."
    docker push "$full_image_name"
    print_success "Image pushed to ACR"

    echo -e "${GREEN}Full image name: $full_image_name${NC}"
}

deploy_container_instance() {
    print_header "Deploying Azure Container Instance"

    local full_image_name="${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${IMAGE_TAG}"

    # Get ACR credentials
    print_info "Retrieving ACR credentials..."
    local acr_username=$(az acr credential show --name "$ACR_NAME" --query username --output tsv)
    local acr_password=$(az acr credential show --name "$ACR_NAME" --query passwords[0].value --output tsv)

    # Delete existing container if it exists
    if az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" &> /dev/null; then
        print_info "Deleting existing container instance..."
        az container delete \
            --resource-group "$RESOURCE_GROUP" \
            --name "$CONTAINER_NAME" \
            --yes \
            --output none
        print_success "Existing container deleted"
    fi

    # Create new container instance
    print_info "Creating container instance (this may take 2-3 minutes)..."
    az container create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$CONTAINER_NAME" \
        --image "$full_image_name" \
        --cpu "$CPU_CORES" \
        --memory "$MEMORY_GB" \
        --registry-login-server "${ACR_NAME}.azurecr.io" \
        --registry-username "$acr_username" \
        --registry-password "$acr_password" \
        --ports 5432 \
        --dns-name-label "$DNS_NAME_LABEL" \
        --ip-address Public \
        --environment-variables \
            POSTGRES_DB="$DB_NAME" \
            POSTGRES_USER="$DB_USER" \
            POSTGRES_PASSWORD="$DB_PASSWORD" \
        --output none

    print_success "Container instance created"
}

get_connection_info() {
    print_header "Connection Information"

    # Get public IP
    local public_ip=$(az container show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$CONTAINER_NAME" \
        --query ipAddress.ip \
        --output tsv)

    # Get FQDN
    local fqdn=$(az container show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$CONTAINER_NAME" \
        --query ipAddress.fqdn \
        --output tsv)

    echo -e "${GREEN}Deployment Complete!${NC}"
    echo ""
    echo -e "${YELLOW}Connection Details:${NC}"
    echo -e "  Public IP:    ${GREEN}$public_ip${NC}"
    echo -e "  FQDN:         ${GREEN}$fqdn${NC}"
    echo -e "  Port:         ${GREEN}5432${NC}"
    echo -e "  Database:     ${GREEN}$DB_NAME${NC}"
    echo -e "  Username:     ${GREEN}$DB_USER${NC}"
    echo -e "  Password:     ${GREEN}$DB_PASSWORD${NC}"
    echo ""
    echo -e "${YELLOW}Connection String:${NC}"
    echo -e "${GREEN}postgresql://$DB_USER:$DB_PASSWORD@$public_ip:5432/$DB_NAME${NC}"
    echo ""
    echo -e "${YELLOW}MCP Configuration (.mcp.json):${NC}"
    echo -e "${BLUE}{"
    echo -e "  \"mcpServers\": {"
    echo -e "    \"postgres-enterprise\": {"
    echo -e "      \"command\": \"C:\\\\Users\\\\kusha\\\\postgresql-mcp\\\\.venv\\\\Scripts\\\\python.exe\","
    echo -e "      \"args\": [\"C:\\\\Users\\\\kusha\\\\postgresql-mcp\\\\mcp_server_enterprise.py\"],"
    echo -e "      \"env\": {"
    echo -e "        \"DATABASE_URL\": \"postgresql://$DB_USER:$DB_PASSWORD@$public_ip:5432/$DB_NAME\""
    echo -e "      }"
    echo -e "    }"
    echo -e "  }"
    echo -e "}${NC}"
    echo ""

    # Save to file
    cat > deployment-info.txt <<EOF
PostgreSQL Azure Container Instance - Deployment Information
=============================================================

Deployment Date: $(date)

Connection Details:
-------------------
Public IP:    $public_ip
FQDN:         $fqdn
Port:         5432
Database:     $DB_NAME
Username:     $DB_USER
Password:     $DB_PASSWORD

Connection String:
------------------
postgresql://$DB_USER:$DB_PASSWORD@$public_ip:5432/$DB_NAME

psql Command:
-------------
psql "postgresql://$DB_USER:$DB_PASSWORD@$public_ip:5432/$DB_NAME"

Azure Resources:
----------------
Resource Group: $RESOURCE_GROUP
ACR Name:       $ACR_NAME
ACI Name:       $CONTAINER_NAME
Location:       $LOCATION

MCP Configuration:
------------------
Update your .mcp.json with:
{
  "mcpServers": {
    "postgres-enterprise": {
      "command": "C:\\\\Users\\\\kusha\\\\postgresql-mcp\\\\.venv\\\\Scripts\\\\python.exe",
      "args": ["C:\\\\Users\\\\kusha\\\\postgresql-mcp\\\\mcp_server_enterprise.py"],
      "env": {
        "DATABASE_URL": "postgresql://$DB_USER:$DB_PASSWORD@$public_ip:5432/$DB_NAME"
      }
    }
  }
}
EOF

    print_success "Connection information saved to 'deployment-info.txt'"
}

test_connection() {
    print_header "Testing Connection"

    local public_ip=$(az container show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$CONTAINER_NAME" \
        --query ipAddress.ip \
        --output tsv)

    print_info "Waiting for PostgreSQL to be ready (may take 30-60 seconds)..."
    sleep 30

    if command -v psql &> /dev/null; then
        print_info "Testing connection with psql..."
        if PGPASSWORD="$DB_PASSWORD" psql -h "$public_ip" -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" &> /dev/null; then
            print_success "Connection test successful!"
        else
            print_error "Connection test failed. Container may still be starting. Try again in a minute."
        fi
    else
        print_info "psql not installed. Skipping connection test."
    fi
}

cleanup_old_resources() {
    print_header "Cleanup (Optional)"
    echo ""
    echo -e "${YELLOW}To delete all resources created by this script, run:${NC}"
    echo -e "${RED}az group delete --name $RESOURCE_GROUP --yes --no-wait${NC}"
    echo ""
}

###############################################################################
# Main Execution
###############################################################################

main() {
    clear
    echo -e "${BLUE}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║   PostgreSQL Azure Container Instance Deployment         ║
║   Automated Deployment Script                            ║
╚═══════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"

    # Run all steps
    check_prerequisites
    create_resource_group
    create_container_registry
    build_and_push_image
    deploy_container_instance
    get_connection_info
    test_connection
    cleanup_old_resources

    echo ""
    print_success "Deployment completed successfully!"
    echo ""
}

# Run main function
main "$@"
