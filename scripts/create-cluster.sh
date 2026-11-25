#!/usr/bin/env bash
# Recreates the GKE cluster and bootstraps GitOps. After this finishes, Argo CD
# deploys log_output/ and the_project/ from git on its own.
#
# Usage: scripts/create-cluster.sh
# Each value is taken from the environment variable if set, otherwise from a
# file (just the value) in $DWK_CONFIG_DIR (default ~/.config/dwk):
#   POSTGRES_PASSWORD  postgres-password  (prompted for if neither is present)
#   WEBHOOK_URL        webhook-url        (Discord webhook, or http://webhook-sink-svc/)
#   BACKUP_BUCKET      backup-bucket      (bucket name without gs://)
# WEBHOOK_FORMAT is an env var only and defaults to discord (or generic).
set -euo pipefail

CLUSTER=${CLUSTER:-dwk-cluster}
ZONE=${ZONE:-europe-north1-b}
PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}
ARGOCD_VERSION=${ARGOCD_VERSION:-stable}
ROLLOUTS_VERSION=${ROLLOUTS_VERSION:-v1.10.2}
NAMESPACE=exercises

: "${PROJECT_ID:?set PROJECT_ID or run gcloud config set project}"

CONFIG_DIR=${DWK_CONFIG_DIR:-$HOME/.config/dwk}

# load_value VAR FILE: if VAR is unset or empty, read it from $CONFIG_DIR/FILE.
load_value() {
  local var=$1 file="$CONFIG_DIR/$2"
  [ -z "${!var:-}" ] || return 0
  [ -f "$file" ] || return 0
  if [ -n "$(find "$file" -perm /077 2>/dev/null)" ]; then
    echo "warning: $file is accessible to others; consider chmod 600" >&2
  fi
  printf -v "$var" '%s' "$(<"$file")"
}

load_value POSTGRES_PASSWORD postgres-password
load_value WEBHOOK_URL webhook-url
load_value BACKUP_BUCKET backup-bucket

if [ -z "${POSTGRES_PASSWORD:-}" ]; then
  read -rsp "Postgres password: " POSTGRES_PASSWORD; echo
fi
[ -n "$POSTGRES_PASSWORD" ] || { echo "empty password" >&2; exit 1; }

: "${BACKUP_BUCKET:?set BACKUP_BUCKET or create $CONFIG_DIR/backup-bucket (bucket name without gs://)}"
: "${WEBHOOK_URL:?set WEBHOOK_URL or create $CONFIG_DIR/webhook-url (Discord webhook, or http://webhook-sink-svc/ with WEBHOOK_FORMAT=generic)}"
WEBHOOK_FORMAT=${WEBHOOK_FORMAT:-discord}

cd "$(dirname "$0")/.."

echo "==> Creating cluster $CLUSTER in $PROJECT_ID ($ZONE)"
gcloud container clusters create "$CLUSTER" \
  --project "$PROJECT_ID" --zone "$ZONE" \
  --release-channel stable \
  --num-nodes 4 --machine-type e2-small \
  --disk-type pd-balanced --disk-size 32 \
  --gateway-api standard \
  --enable-managed-prometheus \
  --logging SYSTEM,WORKLOAD

gcloud container clusters get-credentials "$CLUSTER" --project "$PROJECT_ID" --zone "$ZONE"

# Server-side apply: the Argo CRDs are too big for client-side apply.
echo "==> Installing Argo CD ($ARGOCD_VERSION)"
kubectl create namespace argocd
if [ "$ARGOCD_VERSION" = stable ]; then ref=stable; else ref=$ARGOCD_VERSION; fi
kubectl apply -n argocd --server-side --force-conflicts \
  -f "https://raw.githubusercontent.com/argoproj/argo-cd/$ref/manifests/install.yaml"

echo "==> Installing Argo Rollouts ($ROLLOUTS_VERSION)"
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts --server-side --force-conflicts \
  -f "https://github.com/argoproj/argo-rollouts/releases/download/$ROLLOUTS_VERSION/install.yaml"

kubectl -n argocd rollout status deploy/argocd-server --timeout=5m
kubectl -n argocd rollout status deploy/argocd-repo-server --timeout=5m
kubectl -n argocd rollout status statefulset/argocd-application-controller --timeout=5m
kubectl -n argo-rollouts rollout status deploy/argo-rollouts --timeout=5m

echo "==> Creating namespace and Postgres secret"
kubectl create namespace "$NAMESPACE"
kubectl -n "$NAMESPACE" create secret generic postgres-secret \
  --from-literal=POSTGRES_DB=counterdb \
  --from-literal=POSTGRES_USER=appuser \
  --from-literal=POSTGRES_PASSWORD="$POSTGRES_PASSWORD"

echo "==> Creating staging and production namespaces, secrets and config"
kubectl create namespace staging
kubectl -n staging create secret generic postgres-secret \
  --from-literal=POSTGRES_PASSWORD="$POSTGRES_PASSWORD"
# Staging has no broadcaster-secret (the broadcaster only logs) and no backup.
kubectl create namespace production
kubectl -n production create secret generic postgres-secret \
  --from-literal=POSTGRES_PASSWORD="$POSTGRES_PASSWORD"
kubectl -n production create secret generic broadcaster-secret \
  --from-literal=WEBHOOK_URL="$WEBHOOK_URL" \
  --from-literal=WEBHOOK_FORMAT="$WEBHOOK_FORMAT"
kubectl -n production create configmap backup-config \
  --from-literal=BACKUP_BUCKET="$BACKUP_BUCKET"

echo "==> Registering the Argo CD applications"
kubectl apply -f argocd/log-output-app.yaml
kubectl apply -f argocd/project-staging-app.yaml
kubectl apply -f argocd/project-production-app.yaml

cat <<MSG

Done. Argo CD is syncing log_output/ and the_project/ (staging from main, production from the production branch).
  Watch:     kubectl -n argocd get applications
  UI:        kubectl -n argocd port-forward svc/argocd-server 8080:443   (https://localhost:8080, user: admin)
  Password:  kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d; echo
  Gateway IP (once provisioned): kubectl -n $NAMESPACE get gateway my-gateway
MSG
