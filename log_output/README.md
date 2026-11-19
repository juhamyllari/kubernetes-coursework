# Log output app

## Deployment (exercise 1.1)
The exercise 1.1 version of the app can either be build locally or pulled from Docker Hub. The image can be found at [juhamyllari/timestamp-app](https://hub.docker.com/r/juhamyllari/timestamp-app).

```bash
kubectl create deployment timestamp-deployment --image=juhamyllari/timestamp-app:v4
```

## Deployment (exercise 1.3)
Deploy using the manifest file `log_output/deployment.yaml`:

```bash
kubectl apply -f log_output/deployment.yaml
```

## Deployment (exercises 1.7, 1.9, 1.10, 1.11, 2.1, 2.3, 2.5, 2.7, 3.1, 3.2, 3.3, 3.4)
Deploy by applying the manifest directory `log_output/manifests`:

```bash
kubectl apply -f log_output/manifests
```

## Deployment (4.1+)
From exercise 4.1 onwards, the log output app uses Kustomize: 

```bash
kubectl apply -k .
```

## Deployment (4.4+)
Pingpong is now an Argo Rollouts `Rollout` guarded by an `AnalysisTemplate` (`namespace-cpu-rate`) that queries Prometheus. If the namespace's summed container CPU rate (5m window) exceeds the threshold during the update, the rollout is aborted and the old version stays. The threshold is the `threshold` argument in `manifests/analysistemplate.yaml`.

Prerequisites (once per cluster):

```bash
kubectl create namespace argo-rollouts
kubectl apply --server-side -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/prometheus -n prometheus --create-namespace \
  -f ../the_project/monitoring/prom-values.yaml
```

Then `kubectl apply -k .` as before. Watch an update with `kubectl argo rollouts get rollout pingpong-rollout -n exercises --watch`.
