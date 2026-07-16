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

## Deployment (exercise 1.7)
Deploy by applying the manifest directory `log_output/manifests`:

```bash
kubectl apply -f log_output/manifests
```
