# The "Project" app (a.k.a. the "Todo" app)

## Deployment (exercise 1.2)
The exercise 1.2 version of the app can either be build locally or pulled from Docker Hub. The image can be found at [juhamyllari/todo-app](https://hub.docker.com/r/juhamyllari/todo-app).

```bash
kubectl create deployment todo-deployment --image=juhamyllari/todo-app:v5
```

## Deployment (exercise 1.4)
The exercise 1.4 version of the app is deployed using the `deployment.yaml` manifest file. The image can be found at [juhamyllari/todo-app](https://hub.docker.com/r/juhamyllari/todo-app).

```bash
kubectl apply -f manifests/deployment.yaml
```

## Deployment (exercise 1.6)
The exercise 1.6 version of the app is deployed using the `deployment.yaml` manifest file and the `service.yaml` manifest file. Port forwarding is used to access the app from the local machine. 

```bash
kubectl port-forward service/todo-svc 30080:80 &
kubectl apply -f manifests/deployment.yaml
kubectl apply -f manifests/service.yaml
```

## Deployment (exercise 1.8)
The exercise 1.8 version of the app is deployed by applying the manifest directory:

```bash
kubectl apply -f manifests/
```

## Deployment (exercises 1.12, 1.13, 2.2, 2.4, 2.6, 2.8, 2.9, 2.10)
The local persistent volume requires the existence of the `/tmp/kube` directory on `k3d-k3s-default-agent-0`. The app is deployed by applying the manifest directory:

```bash
kubectl apply -f manifests/
```

## Deployment (exercise 3.5+)
From exercise 3.5 onwards, the project uses Kustomize.

## Deployment (exercise 3.6+)
Pushing to the `main` branch triggers a GitHub Actions workflow that builds and pushes the images and deploys the app.

Kustomize generates the `postgres-secret` Secret from a gitignored `postgres-secret.env` file.
In CI the file is written from the `POSTGRES_PASSWORD` GitHub secret.

## Deployment (exercise 3.7+)
The workflow runs on a push to any branch. The `main` branch deploys to the `project` namespace;
any other branch deploys to a namespace named after the branch (the branch name must be a valid namespace name).
The workflow sets the namespace with `kustomize edit set namespace`, so the manifests do not hardcode one.
Namespaces are not yet removed automatically in exercise 3.7 when a branch is deleted – this will be done in exercise 3.8.

## Cleanup of branch deployments (exercise 3.8+)
Deleting a branch triggers `.github/workflows/cleanup.yaml`, which deletes the branch's namespace.
Only namespaces labelled `deployed-by=branch-pipeline` (set by a Kustomize patch) are deleted, and `project` is never deleted.

## Exercise 3.9: DBaaS vs DIY
When deploying an app to Google Cloud, we have a choice between using a managed database service (DBaaS) or deploying our own database (DIY). The DIY option is cheaper and keeps the database under the team's control. DIY also offers a portability benefit, as the app setup is defined in its entirety by a collection of Kubernetes manifests and can be deployed to any Kubernetes cluster. However, DIY requires more work to set up and maintain, and the team must have the necessary expertise to do so. No automated backups are provided; the team must implement their own backup solution.

The DBaaS option is easier to set up and maintain, and backups can be handled automatically. The main drawback is the additional cost. DBaaS is also less flexible; the team does not have true superuser access to the database. DBaaS may somewhat contribute to vendor lock-in, but this is not a major concern as data can still be exported in the same way as from any other database.






## Exercise 3.10: Daily database backups to Cloud Storage
`manifests/backup-cronjob.yaml` runs daily at 03:00 UTC. An init container (`postgres:16-alpine`) runs `pg_dump -Fc` into an `emptyDir`,
then the main container (`google/cloud-sdk`) uploads the file to `gs://<bucket>/<namespace>/tododb-<timestamp>.pgdump`.
The upload is authorised with Workload Identity Federation for GKE: the pod runs as the Kubernetes ServiceAccount `db-backup`,
which is granted write access to the bucket directly in IAM. No key file is stored.

One-time setup:
```bash
export PROJECT_ID=<your GCP project ID>
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
export BUCKET=<globally unique bucket name, e.g. $PROJECT_ID-todo-db-backups>

# Workload Identity must be enabled on the cluster; this prints $PROJECT_ID.svc.id.goog if it is
# (if empty, see "Cluster creation" below for enabling it on an existing cluster)
gcloud container clusters describe dwk-cluster --zone europe-north1-b --format='value(workloadIdentityConfig.workloadPool)'

gcloud storage buckets create gs://$BUCKET --location=europe-north1 --uniform-bucket-level-access

# Allow the db-backup ServiceAccount of the `project` namespace to create objects in the bucket only
gcloud storage buckets add-iam-policy-binding gs://$BUCKET \
  --role=roles/storage.objectCreator \
  --member="principal://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$PROJECT_ID.svc.id.goog/subject/ns/project/sa/db-backup"
```
The IAM binding names a namespace, so only the `project` namespace (main branch) can upload. Backup jobs in branch namespaces fail with a permission error unless an equivalent binding is added for them.
The bucket name is not committed. Kustomize generates the `backup-config` ConfigMap from a gitignored `backup-config.env` file
containing `BACKUP_BUCKET=<bucket name>` (no `gs://`). In CI the file is written from the `BACKUP_BUCKET` GitHub secret.
For a local `kubectl apply -k .`, create the file yourself.

Test it without waiting for the schedule:
```bash
kubectl -n project create job --from=cronjob/db-backup db-backup-test
kubectl -n project logs job/db-backup-test -c upload
```

### Cluster creation
The cluster is not defined in the repo, so its creation command is recorded here. `--workload-pool` is required for the backups:
it enables Workload Identity and makes new node pools use the GKE metadata server.
```bash
gcloud container clusters create dwk-cluster --zone=europe-north1-b --cluster-version=1.36 \
  --disk-size=32 --num-nodes=4 --machine-type=e2-small \
  --workload-pool=$PROJECT_ID.svc.id.goog
```
On an existing cluster created without the flag, enable it with:
```bash
gcloud container clusters update dwk-cluster --zone europe-north1-b --workload-pool=$PROJECT_ID.svc.id.goog
gcloud container node-pools update <pool-name> --cluster dwk-cluster --zone europe-north1-b --workload-metadata=GKE_METADATA
```
The second command recreates the nodes, so all pods restart.
The bucket and its IAM binding belong to the project, not the cluster, so they survive cluster deletion and keep working with a recreated cluster.
The database contents do not survive; restore the latest dump with `pg_restore`.
