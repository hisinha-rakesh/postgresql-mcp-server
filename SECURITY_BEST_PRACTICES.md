# Security Best Practices for PostgreSQL Deployment

## 🔒 Overview

This guide explains security best practices for deploying PostgreSQL to Azure Container Instance and using it with the MCP server.

---

## 1. Environment Variables & Secrets Management

### ✅ DO: Use .env Files (Never Commit)

**Correct Approach:**
```bash
# .env.deployment (local only, in .gitignore)
POSTGRES_DB=librarydatabase
POSTGRES_USER=rakuser
POSTGRES_PASSWORD=SuperSecure$Pass123!
```

**In .gitignore:**
```gitignore
.env
.env.*
!.env.*.example
*.env
deployment-info.txt
```

### ❌ DON'T: Hardcode Credentials in Dockerfile

**Wrong (Security Risk):**
```dockerfile
# ❌ DON'T DO THIS!
ENV POSTGRES_PASSWORD=mypassword123
```

**Right:**
```dockerfile
# ✅ DO THIS - No hardcoded secrets
# Credentials passed at runtime via environment variables
```

### 🔐 Azure Key Vault Integration (Production)

For production environments, use Azure Key Vault:

```bash
# Store secret in Key Vault
az keyvault secret set \
  --vault-name "my-keyvault" \
  --name "postgres-password" \
  --value "SuperSecure$Pass123!"

# Retrieve in deployment script
DB_PASSWORD=$(az keyvault secret show \
  --vault-name "my-keyvault" \
  --name "postgres-password" \
  --query value -o tsv)
```

---

## 2. Strong Password Policy

### Password Requirements

✅ **Minimum 16 characters**
✅ **Mix of uppercase, lowercase, numbers, symbols**
✅ **No dictionary words**
✅ **No personal information**
✅ **Unique per environment**

### Generate Strong Passwords

**Using PowerShell:**
```powershell
# Generate random 32-character password
$password = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
Write-Host "Generated Password: $password"
```

**Using Bash:**
```bash
# Generate random 32-character password
openssl rand -base64 32
```

**Using Python:**
```python
import secrets
import string

# Generate 32-character password
alphabet = string.ascii_letters + string.digits + string.punctuation
password = ''.join(secrets.choice(alphabet) for i in range(32))
print(f"Generated Password: {password}")
```

---

## 3. Network Security

### Azure Firewall Rules

**Restrict access to specific IPs:**

```bash
# Add your IP to whitelist
MY_IP=$(curl -s https://api.ipify.org)

az container create \
  --resource-group rg-postgres-mcp \
  --name aci-postgres-library \
  --image ... \
  --ports 5432 \
  --ip-address Public \
  --environment-variables ... \
  # Note: ACI doesn't support firewall rules directly
  # Use Azure Network Security Groups or Virtual Networks instead
```

### Use Azure Virtual Network (Recommended for Production)

```bash
# Create Virtual Network
az network vnet create \
  --resource-group rg-postgres-mcp \
  --name vnet-postgres \
  --address-prefix 10.0.0.0/16 \
  --subnet-name subnet-postgres \
  --subnet-prefix 10.0.1.0/24

# Deploy container to VNet (private IP only)
az container create \
  --resource-group rg-postgres-mcp \
  --name aci-postgres-library \
  --image ... \
  --vnet vnet-postgres \
  --subnet subnet-postgres \
  --ip-address Private
```

### SSL/TLS Encryption

**Enable SSL in connection string:**
```
postgresql://user:pass@host:5432/db?sslmode=require
```

**SSL Modes:**
- `require` - Always use SSL (recommended)
- `verify-ca` - Verify certificate authority
- `verify-full` - Verify CA and hostname

---

## 4. Database User Permissions

### Principle of Least Privilege

**Create dedicated user for MCP server:**

```sql
-- Connect as admin
psql "postgresql://rakuser:rakpassword@host:5432/librarydatabase"

-- Create dedicated MCP user
CREATE USER mcp_app_user WITH PASSWORD 'Different$Strong$Password123!';

-- Grant only necessary permissions
GRANT CONNECT ON DATABASE librarydatabase TO mcp_app_user;
GRANT USAGE ON SCHEMA public TO mcp_app_user;

-- For read-only access
GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_app_user;

-- For read-write access (but no DDL)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mcp_app_user;

-- For future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO mcp_app_user;

-- NEVER grant these unless absolutely necessary:
-- REVOKE CREATE ON SCHEMA public FROM mcp_app_user;
-- REVOKE DROP ON ALL TABLES IN SCHEMA public FROM mcp_app_user;
```

### Separate Users by Environment

```sql
-- Development
CREATE USER mcp_dev_user WITH PASSWORD 'DevPass123!';

-- Staging
CREATE USER mcp_staging_user WITH PASSWORD 'StagingPass456!';

-- Production
CREATE USER mcp_prod_user WITH PASSWORD 'ProdPass789!';
```

---

## 5. MCP Server Configuration Security

### Secure .mcp.json

**Location:** `~/.mcp.json` or `C:\Users\kusha\.mcp.json`

**Permissions:**
```bash
# Linux/Mac: Restrict to owner only
chmod 600 ~/.mcp.json

# Windows: Right-click → Properties → Security → Advanced
# Remove all users except yourself
```

### Environment-Specific Configurations

**Development:**
```json
{
  "mcpServers": {
    "postgres-dev": {
      "command": "python",
      "args": ["mcp_server_enterprise.py"],
      "env": {
        "DATABASE_URL": "postgresql://mcp_dev_user:DevPass123!@localhost:5432/dev_db"
      }
    }
  }
}
```

**Production:**
```json
{
  "mcpServers": {
    "postgres-prod": {
      "command": "python",
      "args": ["mcp_server_enterprise.py"],
      "env": {
        "DATABASE_URL": "postgresql://mcp_prod_user:ProdPass789!@prod-host:5432/prod_db?sslmode=require"
      }
    }
  }
}
```

---

## 6. Audit Logging

### Enable PostgreSQL Logging

```sql
-- Enable statement logging (log all modifications)
ALTER SYSTEM SET log_statement = 'mod';

-- Log all connections
ALTER SYSTEM SET log_connections = 'on';
ALTER SYSTEM SET log_disconnections = 'on';

-- Log slow queries (>1 second)
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- Reload configuration
SELECT pg_reload_conf();
```

### View Container Logs (Azure)

```bash
# View logs
az container logs \
  --resource-group rg-postgres-mcp \
  --name aci-postgres-library \
  --follow

# Export logs
az container logs \
  --resource-group rg-postgres-mcp \
  --name aci-postgres-library > postgres-logs.txt
```

---

## 7. Backup & Disaster Recovery

### Regular Backups

```bash
# Using MCP server backup tool
# In Claude Desktop:
"Backup the librarydatabase to C:\backups with custom format"

# Manual backup with pg_dump
pg_dump -h host -U user -d librarydatabase -Fc -f backup_$(date +%Y%m%d).dump
```

### Encrypted Backups

```bash
# Encrypt backup with GPG
pg_dump -h host -U user -d librarydatabase | \
  gzip | \
  gpg --encrypt --recipient your@email.com > \
  backup_$(date +%Y%m%d).dump.gz.gpg
```

### Azure Backup Integration

```bash
# Upload to Azure Blob Storage
az storage blob upload \
  --account-name mystorageaccount \
  --container-name backups \
  --name "backup_$(date +%Y%m%d).dump" \
  --file backup_$(date +%Y%m%d).dump \
  --auth-mode login
```

---

## 8. Regular Security Updates

### Update Container Image

```bash
# Pull latest PostgreSQL image
docker pull postgres:17-alpine

# Rebuild and redeploy
./deploy-to-azure.sh
```

### Monitor Security Advisories

- **PostgreSQL Security:** https://www.postgresql.org/support/security/
- **Azure Security:** https://azure.microsoft.com/en-us/updates/
- **Docker Security:** https://www.docker.com/blog/

---

## 9. Secrets Rotation

### Rotate Database Password

```sql
-- 1. Create new password
-- 2. Update in Azure Key Vault or .env file
-- 3. Change password in database
ALTER USER rakuser WITH PASSWORD 'NewSecurePassword456!';

-- 4. Update MCP configuration
-- 5. Restart MCP server
```

### Automated Rotation (Production)

```bash
# Scheduled script to rotate passwords every 90 days
# Store in cron or Azure Automation
```

---

## 10. Security Checklist

### Before Deployment

- [ ] Strong password set in `.env.deployment`
- [ ] `.env.deployment` added to `.gitignore`
- [ ] No hardcoded secrets in Dockerfile
- [ ] Reviewed Azure region for compliance
- [ ] SSL/TLS enabled in connection string

### After Deployment

- [ ] Changed default admin password
- [ ] Created dedicated application user
- [ ] Applied least privilege permissions
- [ ] Enabled audit logging
- [ ] Set up backup schedule
- [ ] Restricted network access (VNet or firewall)
- [ ] Documented connection details securely
- [ ] Set up monitoring/alerts

### Ongoing

- [ ] Regular password rotation (90 days)
- [ ] Review audit logs weekly
- [ ] Update container images monthly
- [ ] Test backup restoration quarterly
- [ ] Security vulnerability scanning
- [ ] Access review (remove unused accounts)

---

## 🚨 Security Incident Response

### If Credentials Are Compromised

1. **Immediately rotate passwords:**
   ```sql
   ALTER USER rakuser WITH PASSWORD 'NewEmergencyPassword!';
   ```

2. **Review audit logs:**
   ```sql
   SELECT * FROM pg_stat_activity;
   ```

3. **Terminate suspicious connections:**
   ```sql
   SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE usename = 'suspicious_user';
   ```

4. **Update all configurations:**
   - `.mcp.json`
   - `.env.deployment`
   - Azure Key Vault

5. **Restore from backup if data compromised**

---

## 📚 Additional Resources

- **OWASP Top 10:** https://owasp.org/www-project-top-ten/
- **PostgreSQL Security:** https://www.postgresql.org/docs/current/security.html
- **Azure Security Best Practices:** https://docs.microsoft.com/azure/security/
- **Docker Security:** https://docs.docker.com/engine/security/

---

**Remember:** Security is not a one-time setup, it's an ongoing process!
