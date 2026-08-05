# Kubernetes Labs

## Objective

Learn the fundamentals of Kubernetes by deploying, exposing, and managing a containerized application on a local or cloud-based Kubernetes cluster.

## Prerequisites

- Access to a Kubernetes cluster (e.g., [Minikube](https://minikube.sigs.k8s.io/docs/), [Kind](https://kind.sigs.k8s.io/), or a managed cloud cluster)
- kubectl CLI installed and configured
- Docker installed
- Basic understanding of containers (see [Docker Labs](../docker/README.md))

## Scenario

You are tasked with deploying a simple web application to Kubernetes, exposing it via a Service, and scaling it to handle increased load. This lab will guide you through creating Kubernetes manifests, applying them, and managing application lifecycle.

## Steps

1. **Clone the Example Application**
   ```sh
   git clone https://github.com/docker/getting-started.git
   cd getting-started
   ```

2. **Build and Push the Docker Image**
   - Build the image (reuse from Docker lab):
     ```sh
     docker build -t my-app:latest .
     ```
   - (Optional) Tag and push to a container registry if your cluster cannot access local images.

3. **Create a Kubernetes Deployment Manifest**
   - Create a file named `deployment.yaml`:
     ```yaml
     apiVersion: apps/v1
     kind: Deployment
     metadata:
       name: my-app
     spec:
       replicas: 2
       selector:
         matchLabels:
           app: my-app
       template:
         metadata:
           labels:
             app: my-app
         spec:
           containers:
           - name: my-app
             image: my-app:latest
             ports:
             - containerPort: 3000
     ```

4. **Apply the Deployment**
   ```sh
   kubectl apply -f deployment.yaml
   ```

5. **Create a Service Manifest**
   - Create a file named `service.yaml`:
     ```yaml
     apiVersion: v1
     kind: Service
     metadata:
       name: my-app-service
     spec:
       type: NodePort
       selector:
         app: my-app
       ports:
         - protocol: TCP
           port: 3000
           targetPort: 3000
     ```

6. **Apply the Service**
   ```sh
   kubectl apply -f service.yaml
   ```

7. **Access the Application**
   - Get the NodePort:
     ```sh
     kubectl get service my-app-service
     ```
   - Access the app at `http://<NodeIP>:<NodePort>`. For Minikube, use:
     ```sh
     minikube service my-app-service
     ```

8. **Scale the Deployment**
   ```sh
   kubectl scale deployment my-app --replicas=4
   ```

9. **Check Pod Status**
   ```sh
   kubectl get pods
   ```

## Validation

- The application is accessible via the Service endpoint.
- `kubectl get pods` shows the desired number of running pods.
- Scaling the deployment increases/decreases the number of pods as expected.

## Common Failure Modes

- **Image pull errors:** Ensure the image is accessible to the cluster (push to a registry if needed).
- **Port conflicts:** Verify Service and Deployment ports match.
- **Pods not starting:** Check pod logs with `kubectl logs <pod-name>` for errors.

## Cleanup

- Delete resources:
  ```sh
  kubectl delete -f service.yaml
  kubectl delete -f deployment.yaml
  ```
- Remove the cloned repository:
  ```sh
  cd ..
  rm -rf getting-started
  ```

## Related Topics

- [Cloud-Native Patterns: Service Discovery](../../patterns/service-discovery.md)
- [Case Studies: Spotify Kubernetes Migration](../../case-studies/spotify/README.md)
- [Learning Path: Kubernetes](../../docs/06-kubernetes.md)
- [Glossary](../../docs/glossary.md)
- [Open Source Projects](../../resources/open-source-projects.md)

---

**Next Lab:** Proceed to [labs/terraform/README.md](../terraform/README.md) to learn about infrastructure as code and automation.