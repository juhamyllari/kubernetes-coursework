#!/usr/bin/env bash
# Recreates the GKE cluster and bootstraps GitOps. After this finishes, Argo CD
# deploys log_output/ from git on its own.
#
# Usage: POSTGRES_PASSWORD=... scripts/create-cluster.sh
# (if POSTGRES_PASSWORD is unset, you are prompted for it)
set -euo pipefail

CLUSTER=${CLUSTER:-dwk-cluster}
ZONE=${ZONE:-europe-north1-b}
PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}
ARGOCD_VERSION=${ARGOCD_VERSION:-stable}
ROLLOUTS_VERSION=${ROLLOUTS_VERSION:-v1.10.2}
NAMESPACE=exercises

: "${PROJECT_ID:?set PROJECT_ID or run gcloud config set project}"
if [ -z "${POSTGRES_PASSWORD:-}" ]; then
  read -rsp "Postgres password: " POSTGRES_PASSWORD; echo
fi
[ -n "$POSTGRES_PASSWORD" ] || { echo "empty password" >&2; exit 1; }

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

echo "==> Registering the Argo CD application"
kubectl apply -f argocd/log-output-app.yaml

cat <<MSG

Done. Argo CD is syncing log_output/ from main.
  Watch:     kubectl -n argocd get applications
  UI:        kubectl -n argocd port-forward svc/argocd-server 8080:443   (https://localhost:8080, user: admin)
  Password:  kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d; echo
  Gateway IP (once provisioned): kubectl -n $NAMESPACE get gateway my-gateway
MSG
