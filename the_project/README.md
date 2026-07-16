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
