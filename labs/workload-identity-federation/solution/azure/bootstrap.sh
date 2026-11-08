#!/usr/bin/env bash
# One-time platform bootstrap for the charity site on Azure Container Apps.
#
# Run by the subscription owner, once, from Cloud Shell or a laptop. It is NOT part of the
# deployment pipeline: registering resource providers and granting roles are subscription-level
# actions, and the deployment identity must not hold the rights to do them.
#
#   SUBSCRIPTION_ID=... GH_OWNER=... GH_REPO=... ./bootstrap.sh
#
# Idempotent: each step checks the current state first. Reference only; not executed by the lab.
set -euo pipefail

: "${SUBSCRIPTION_ID:?set SUBSCRIPTION_ID}" "${GH_OWNER:?set GH_OWNER}" "${GH_REPO:?set GH_REPO}"
RG="${RG:-rg-sharetable}"
LOCATION="${LOCATION:-swedencentral}"
APP="${APP:-sharetable-app}"
IDENTITY="${IDENTITY:-github-sharetable-deploy}"
ENVIRONMENT="${ENVIRONMENT:-production}"       # GitHub environment that may deploy
WAIT_MINUTES="${WAIT_MINUTES:-15}"

az account set --subscription "$SUBSCRIPTION_ID"

# 1. Resource providers. Container Apps needs Microsoft.App, and Microsoft.OperationalInsights for
#    its log workspace. "Registering" is not "Registered": the containerapp CLI commands refuse to
#    run until the state is Registered, even if existing apps keep serving.
for rp in Microsoft.App Microsoft.OperationalInsights; do
  state="$(az provider show -n "$rp" --query registrationState -o tsv)"
  if [[ "$state" != "Registered" ]]; then
    az provider register -n "$rp" >/dev/null
  fi
done
deadline=$(( $(date +%s) + WAIT_MINUTES * 60 ))
for rp in Microsoft.App Microsoft.OperationalInsights; do
  until [[ "$(az provider show -n "$rp" --query registrationState -o tsv)" == "Registered" ]]; do
    if (( $(date +%s) > deadline )); then
      echo "provider $rp is still $(az provider show -n "$rp" --query registrationState -o tsv) after $WAIT_MINUTES minutes" >&2
      echo "diagnose: registration operations in the activity log, and policies that restrict locations:" >&2
      az monitor activity-log list --offset 7d \
        --query "[?contains(operationName.value, '$rp/register')].[eventTimestamp, status.value, subStatus.value]" -o table >&2 || true
      az policy assignment list --query "[].displayName" -o table >&2 || true
      echo "This needs the platform owner or Azure support. No pipeline step can fix it." >&2
      exit 3
    fi
    sleep 20
  done
done

# 2. Deployment identity: a user-assigned managed identity, federated with GitHub Actions.
az identity show -g "$RG" -n "$IDENTITY" >/dev/null 2>&1 \
  || az identity create -g "$RG" -n "$IDENTITY" -l "$LOCATION" >/dev/null
CLIENT_ID="$(az identity show -g "$RG" -n "$IDENTITY" --query clientId -o tsv)"
PRINCIPAL_ID="$(az identity show -g "$RG" -n "$IDENTITY" --query principalId -o tsv)"

# 3. Trust exactly one subject: the production environment of this repository, in the immutable
#    format (owner and repository IDs never change or get reused). Repositories created after
#    15 July 2026 use this format by default; older ones after opting in.
OWNER_ID="${GH_OWNER_ID:-$(gh api "users/$GH_OWNER" --jq .id)}"
REPO_ID="${GH_REPO_ID:-$(gh api "repos/$GH_OWNER/$GH_REPO" --jq .id)}"
SUBJECT="repo:${GH_OWNER}@${OWNER_ID}/${GH_REPO}@${REPO_ID}:environment:${ENVIRONMENT}"
if ! az identity federated-credential show -g "$RG" --identity-name "$IDENTITY" -n "github-$ENVIRONMENT" >/dev/null 2>&1; then
  az identity federated-credential create -g "$RG" --identity-name "$IDENTITY" -n "github-$ENVIRONMENT" \
    --issuer "https://token.actions.githubusercontent.com" \
    --subject "$SUBJECT" \
    --audiences "api://AzureADTokenExchange" >/dev/null
fi

# 4. Least privilege: the identity may change this one app, nothing else. The scope is written out,
#    so this step does not depend on a containerapp command succeeding. If an update fails with
#    LinkedAuthorizationFailed on the managed environment, also grant
#    Microsoft.App/managedEnvironments/join/action on the environment (custom role).
SCOPE="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RG/providers/Microsoft.App/containerApps/$APP"
if [[ -z "$(az role assignment list --assignee "$PRINCIPAL_ID" --scope "$SCOPE" --role Contributor --query '[].id' -o tsv)" ]]; then
  az role assignment create --assignee-object-id "$PRINCIPAL_ID" --assignee-principal-type ServicePrincipal \
    --role Contributor --scope "$SCOPE" >/dev/null
fi

cat <<OUT
Set these as variables of the GitHub environment "$ENVIRONMENT" (they are identifiers, not secrets):
  AZURE_CLIENT_ID=$CLIENT_ID
  AZURE_TENANT_ID=$(az account show --query tenantId -o tsv)
  AZURE_SUBSCRIPTION_ID=$SUBSCRIPTION_ID
Trusted subject: $SUBJECT
Role: Contributor on $SCOPE
OUT
