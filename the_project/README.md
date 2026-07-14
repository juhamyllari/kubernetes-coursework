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
