#!/usr/bin/env bash
# Deletes the GKE cluster (and with it all in-cluster data). Artifact Registry
# images and the GitHub/workload identity setup are untouched.
# The Gateways are deleted first: their Google load balancers and static IPs live
# outside the cluster and would otherwise leak, eating the project's quota of
# 8 global static addresses.
set -euo pipefail

CLUSTER=${CLUSTER:-dwk-cluster}
ZONE=${ZONE:-europe-north1-b}
PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}
: "${PROJECT_ID:?set PROJECT_ID or run gcloud config set project}"

read -rp "Delete cluster $CLUSTER in $PROJECT_ID? [y/N] " ans
[ "$ans" = y ] || exit 1
gcloud container clusters get-credentials "$CLUSTER" --project "$PROJECT_ID" --zone "$ZONE"
# Applications have no cascade finalizer, so this leaves the resources in place
# but stops Argo CD from recreating the Gateways.
kubectl -n argocd delete applications --all --wait=true || true
# Returns once the GKE gateway controller has removed the load balancers.
kubectl delete gateways.gateway.networking.k8s.io --all --all-namespaces --wait=true --timeout=15m
gcloud container clusters delete "$CLUSTER" --project "$PROJECT_ID" --zone "$ZONE" --quiet
