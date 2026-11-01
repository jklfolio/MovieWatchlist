# MovieWatchlist

MovieWatchlist is a cloud-native application built with two Python FastAPI
microservices and MongoDB, deployed to Kubernetes using Docker containers.

## Architecture

The application consists of:

- **Movie Service**: A FastAPI REST service that stores and manages movies in MongoDB.
- **Watchlist Service**: A FastAPI service that provides a browser interface and
  consumes the Movie Service REST API using HTTPX.
- **MongoDB**: A document database used by the Movie Service.
- **Kubernetes**: Deploys, scales, and manages the application components.

```text
Browser
   |
   v
Watchlist Service (FastAPI)
   |
   | REST request using HTTPX
   v
Movie Service (FastAPI)
   |
   v
MongoDB
```

## Services

### Movie Service

The Movie Service provides the following endpoints:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Checks service and MongoDB connectivity |
| POST | `/movies` | Adds a movie |
| GET | `/movies` | Lists all movies |
| PATCH | `/movies/{movie_id}/watched` | Marks a movie as watched |

### Watchlist Service

The Watchlist Service provides:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Checks service health |
| GET | `/` | Browser interface |
| POST | `/add-movie` | Adds a movie through the Movie Service |
| POST | `/watchlists` | Creates a watchlist |
| GET | `/watchlists` | Lists watchlists |
| GET | `/watchlists/{id}` | Gets one watchlist |
| POST | `/watchlists/{id}/movies` | Adds a movie through the Movie Service |

## Docker Images

The application uses two custom Docker images:

- `kanniga/moviewatchlist-movie-service:v1`
- `kanniga/moviewatchlist-watchlist-service:v1`

MongoDB uses the official `mongo:7` image.

## Local Development with Docker Compose

From the `movie-service` directory:

```bash
docker compose up -d
```

The Movie Service is available at:

```text
http://127.0.0.1:8000/docs
```

The Watchlist Service is available at:

```text
http://127.0.0.1:8001/docs
```

The browser interface is available at:

```text
http://127.0.0.1:8001/
```

## Kubernetes Deployment

Ensure Docker Desktop Kubernetes is enabled, then apply the manifests:

```bash
cd k8s
kubectl apply -f .
```

Check the resources:

```bash
kubectl get pods
kubectl get deployments
kubectl get services
kubectl get pvc
```

Access the Watchlist Service locally:

```bash
kubectl port-forward svc/watchlist-service 8001:8000
```

Then open:

```text
http://127.0.0.1:8001/
```

## Scaling

Both application services are deployed with two replicas. They can be scaled independently:

```bash
kubectl scale deployment movie-service --replicas=3
kubectl scale deployment watchlist-service --replicas=3
```

Verify:

```bash
kubectl get deployments
kubectl get pods
```

## Data Persistence

MongoDB uses a Kubernetes `PersistentVolumeClaim` mounted at `/data/db`.
This allows movie data to remain available when the MongoDB pod is restarted.

## Design Benefits

- **Microservices**: Movie and Watchlist functionality are separated into independent services.
- **REST communication**: The Watchlist Service consumes the Movie Service through HTTP.
- **Scalability**: Each application service can be scaled independently.
- **Persistence**: MongoDB data is retained using a PersistentVolumeClaim.
- **Containerization**: Docker ensures consistent execution across local and Kubernetes environments.
- **Service discovery**: Kubernetes Services provide stable internal DNS names.

## Challenges and Mitigations

| Challenge | Mitigation |
|---|---|
| Database availability | The Movie Service uses a health endpoint and MongoDB connection timeout |
| Service-to-service failures | HTTP requests use timeouts and return clear HTTP error responses |
| Data loss | MongoDB uses persistent storage |
| Configuration differences | MongoDB and Movie Service URLs are supplied through environment variables |
| Unauthorized access | In a production system, API authentication, network policies, and secrets management would be added |

## Future Improvements

- Store watchlists in MongoDB rather than in memory.
- Add authentication and authorization.
- Add automated API and integration tests.
- Add Kubernetes liveness and readiness probes.
- Use Kubernetes Secrets for database credentials.
- Add centralized logging and monitoring.
