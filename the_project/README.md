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
