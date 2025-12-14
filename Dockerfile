# PostgreSQL 17 Dockerfile for Azure Container Instance
FROM postgres:17-alpine

# Metadata
LABEL maintainer="your-email@example.com"
LABEL description="PostgreSQL 17 database for MCP server"

# NOTE: Database credentials should be passed at runtime via environment variables
# DO NOT hardcode passwords in this Dockerfile!
# Use: docker run -e POSTGRES_PASSWORD=<password> ...

# Optional: Copy initialization scripts
# COPY ./init-scripts/*.sql /docker-entrypoint-initdb.d/

# Expose PostgreSQL default port
EXPOSE 5432

# PostgreSQL will start automatically
# The official postgres image handles the CMD
# Required environment variables (to be set at runtime):
#   POSTGRES_DB - Database name
#   POSTGRES_USER - Database username
#   POSTGRES_PASSWORD - Database password
