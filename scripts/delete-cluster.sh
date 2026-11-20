#!/usr/bin/env bash
# Deletes the GKE cluster (and with it all in-cluster data). Artifact Registry
# images and the GitHub/workload identity setup are untouched.
set -euo pipefail

CLUSTER=${CLUSTER:-dwk-cluster}
ZONE=${ZONE:-europe-north1-b}
PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}
: "${PROJECT_ID:?set PROJECT_ID or run gcloud config set project}"

read -rp "Delete cluster $CLUSTER in $PROJECT_ID? [y/N] " ans
[ "$ans" = y ] || exit 1
gcloud container clusters delete "$CLUSTER" --project "$PROJECT_ID" --zone "$ZONE" --quiet
