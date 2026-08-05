# Docker Labs

## Objective

Gain hands-on experience with container fundamentals by building, running, and managing Docker containers in a vendor-neutral environment.

## Prerequisites

- Docker installed on your local machine ([Get Docker](https://docs.docker.com/get-docker/))
- Basic command-line proficiency
- Git installed

## Scenario

You are tasked with containerizing a simple web application and running it locally. This lab will guide you through creating a Dockerfile, building an image, running a container, and managing container lifecycle operations.

## Steps

1. **Clone the Example Application**
   ```sh
   git clone https://github.com/docker/getting-started.git
   cd getting-started
   ```

2. **Review the Application**
   - Explore the source code and note the application entry point.

3. **Create a Dockerfile**
   - In the project root, create a file named `Dockerfile` with the following content:
     ```Dockerfile
     FROM node:18-alpine
     WORKDIR /app
     COPY . .
     RUN npm install
     EXPOSE 3000
     CMD ["npm", "start"]
     ```

4. **Build the Docker Image**
   ```sh
   docker build -t my-app:latest .
   ```

5. **Run the Container**
   ```sh
   docker run -d -p 3000:3000 --name my-running-app my-app:latest
   ```

6. **Access the Application**
   - Open [http://localhost:3000](http://localhost:3000) in your browser.

7. **List Running Containers**
   ```sh
   docker ps
   ```

8. **Stop and Remove the Container**
   ```sh
   docker stop my-running-app
   docker rm my-running-app
   ```

## Validation

- The application is accessible at [http://localhost:3000](http://localhost:3000).
- `docker ps` shows the running container.
- Stopping and removing the container works without errors.

## Common Failure Modes

- **Port already in use:** Change the host port in the `docker run` command if 3000 is occupied.
- **Build errors:** Ensure Dockerfile syntax is correct and dependencies are installed.
- **Application not accessible:** Check Docker logs with `docker logs my-running-app` for errors.

## Cleanup

- Remove the Docker image:
  ```sh
  docker rmi my-app:latest
  ```
- Delete the cloned repository:
  ```sh
  cd ..
  rm -rf getting-started
  ```

## Related Topics

- [Cloud-Native Patterns: Stateless Services](../../patterns/stateless-services.md)
- [Case Studies: Netflix Containerization](../../case-studies/netflix/README.md)
- [Learning Path: Containers](../../docs/05-containers.md)
- [Glossary](../../docs/glossary.md)
- [Open Source Projects](../../resources/open-source-projects.md)

---

**Next Lab:** Proceed to [labs/kubernetes/README.md](../kubernetes/README.md) to learn about orchestrating containers at scale.