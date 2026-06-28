# Route Optimization Platform

> Vehicle Routing Problem with Time Windows and Capacity Constraints (CVRPTW)

## Description

A logistics optimization system that solves the CVRPTW problem —
efficient routing of vehicles considering time windows and load capacity.

## Team

| Name | Email |
|------|-------|
| Maksim Potushinskii | m.potushinskii@innopolis.university |
| Dania Galieva | da.galieva@innopolis.university |
| Anastasiia Glinskaia | a.glinskaia@innopolis.university |
| Timur Iusupov | t.iusupov@innopolis.university |
| Marsel Tukhvatullin | m.tukhvatullin@innopolis.university |

## Setup Steps

1. Clone the repository:
```
git clone https://github.com/iu-students/route-optimization-platform.git
cd route-optimization-platform
```
2. Create `.env` file:

`API_KEY` - The master authentication key required for all API requests.

```
cp .env.example .env
```

3. Start with Docker Compose:
```
This command builds the Docker images (if not already built) and starts all required services in detached mode. The platform will run in the background.
docker compose up --build -d
```

4. Verify :
```
curl http://localhost:5000/health
```

# Swagger UI

After starting the application, open `http://localhost:5000/docs` in your browser to access Swagger UI.

## API Version

Use the dropdown at the top of Swagger UI to switch between MVP versions. Current active version: **v2**

## Available Endpoints

**POST /solve** — Start route optimization calculation. Sends route parameters to the server.

**GET /solution** — Get the computed optimal route after `/solve` completes.

**GET /health** — Check server status.

## Authentication

All endpoints except `/health` require API key authentication. Include in request headers:
`X-API-Key: your-api-key`

The API key is set in the `.env` file.
## Weekly reports

Week 2: https://github.com/iu-students/route-optimization-platform/blob/main/reports/week2/README.md

Week 3: https://github.com/iu-students/route-optimization-platform/blob/main/reports/week3/README.md

