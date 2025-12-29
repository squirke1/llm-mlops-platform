# Secrets Management

This directory contains Kubernetes Secret templates for the MLOps platform.

##  Security Warning

**NEVER commit actual secrets to version control!**

The `secrets.yaml` file contains template values only. In production:
1. Use strong, randomly generated passwords
2. Store secrets in a secure vault (AWS Secrets Manager, HashiCorp Vault, etc.)
3. Create secrets directly in Kubernetes using `kubectl create secret`

## Creating Secrets in Production

### Method 1: kubectl (Recommended for Development)

```bash
# MLflow database secrets
kubectl create secret generic mlflow-secrets \
  --from-literal=db-username=mlflow \
  --from-literal=db-password=$(openssl rand -base64 32)

# PostgreSQL secrets
kubectl create secret generic postgres-secrets \
  --from-literal=postgres-password=$(openssl rand -base64 32) \
  --from-literal=postgres-user=mlflow \
  --from-literal=postgres-db=mlflow

# API secrets
kubectl create secret generic api-secrets \
  --from-literal=api-key=$(openssl rand -hex 32)
```

### Method 2: AWS Secrets Manager (Recommended for Production)

1. **Store secrets in AWS Secrets Manager:**

```bash
# Create MLflow database secret
aws secretsmanager create-secret \
  --name mlops-platform/mlflow/db-credentials \
  --secret-string '{"username":"mlflow","password":"<strong-password>"}'

# Create PostgreSQL secret
aws secretsmanager create-secret \
  --name mlops-platform/postgres/credentials \
  --secret-string '{"username":"mlflow","password":"<strong-password>","database":"mlflow"}'

# Create API secret
aws secretsmanager create-secret \
  --name mlops-platform/api/key \
  --secret-string '{"api-key":"<your-api-key>"}'
```

2. **Install AWS Secrets Manager CSI Driver:**

```bash
# Add Secrets Store CSI Driver
helm repo add secrets-store-csi-driver https://kubernetes-sigs.github.io/secrets-store-csi-driver/charts
helm install csi-secrets-store secrets-store-csi-driver/secrets-store-csi-driver \
  --namespace kube-system

# Add AWS provider
kubectl apply -f https://raw.githubusercontent.com/aws/secrets-store-csi-driver-provider-aws/main/deployment/aws-provider-installer.yaml
```

3. **Create SecretProviderClass:**

See `aws-secret-provider.yaml` for configuration.

### Method 3: HashiCorp Vault

1. **Store secrets in Vault:**

```bash
# Enable KV secrets engine
vault secrets enable -path=mlops-platform kv-v2

# Write secrets
vault kv put mlops-platform/mlflow db-username=mlflow db-password=<strong-password>
vault kv put mlops-platform/postgres postgres-user=mlflow postgres-password=<strong-password> postgres-db=mlflow
vault kv put mlops-platform/api api-key=<your-api-key>
```

2. **Configure Vault Agent Injector:**

```bash
# Install Vault
helm repo add hashicorp https://helm.releases.hashicorp.com
helm install vault hashicorp/vault --set "injector.enabled=true"
```

3. **Annotate pods to inject secrets:**

See `vault-annotations-example.yaml` for pod annotations.

## Rotating Secrets

### Automated Rotation (Production)

Use AWS Secrets Manager or Vault automatic rotation:

```bash
# AWS Secrets Manager
aws secretsmanager rotate-secret \
  --secret-id mlops-platform/postgres/credentials \
  --rotation-lambda-arn arn:aws:lambda:region:account:function:SecretsManagerRotation
```

### Manual Rotation

```bash
# Update the secret
kubectl create secret generic postgres-secrets \
  --from-literal=postgres-password=$(openssl rand -base64 32) \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart deployments to pick up new secrets
kubectl rollout restart deployment mlflow-server
kubectl rollout restart deployment postgres
```

## Verifying Secrets

```bash
# List secrets
kubectl get secrets

# View secret (base64 encoded)
kubectl get secret postgres-secrets -o yaml

# Decode secret value
kubectl get secret postgres-secrets -o jsonpath='{.data.postgres-password}' | base64 -d
```

## Best Practices

1. **Use Strong Passwords**
   - Minimum 32 characters
   - Use cryptographically secure random generation
   - Never use dictionary words or patterns

2. **Principle of Least Privilege**
   - Create separate secrets for each service
   - Use Kubernetes RBAC to restrict access
   - Only mount secrets into pods that need them

3. **Regular Rotation**
   - Rotate secrets every 90 days
   - Automate rotation where possible
   - Test rotation process in staging first

4. **Audit and Monitoring**
   - Enable audit logging for secret access
   - Alert on unauthorized access attempts
   - Track secret age and rotation status

5. **Encryption at Rest**
   - Enable Kubernetes secrets encryption
   - Use KMS for key management
   - Encrypt etcd backups

6. **Secret Scanning**
   - Use git-secrets or similar tools
   - Scan code for accidentally committed secrets
   - Implement pre-commit hooks

## Environment Variables

Update deployments to use secrets as environment variables:

```yaml
env:
  - name: POSTGRES_PASSWORD
    valueFrom:
      secretKeyRef:
        name: postgres-secrets
        key: postgres-password
  - name: POSTGRES_USER
    valueFrom:
      secretKeyRef:
        name: postgres-secrets
        key: postgres-user
```

## Troubleshooting

### Secret Not Found

```bash
# Check if secret exists
kubectl get secret postgres-secrets

# Check secret contents
kubectl describe secret postgres-secrets
```

### Pod Can't Access Secret

```bash
# Check pod events
kubectl describe pod <pod-name>

# Verify RBAC permissions
kubectl auth can-i get secrets --as=system:serviceaccount:default:default
```

### Secret Not Updating

```bash
# Force pod restart to pick up changes
kubectl delete pod <pod-name>

# Or use rollout restart
kubectl rollout restart deployment <deployment-name>
```

## References

- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)
- [HashiCorp Vault](https://www.vaultproject.io/)
- [Secrets Store CSI Driver](https://secrets-store-csi-driver.sigs.k8s.io/)
