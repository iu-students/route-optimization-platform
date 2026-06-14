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
git checkout 1-interface
```

2. Create `.env` file from the example:
```
cp .env.example .env
```

3. Start with Docker Compose:
```
docker compose up --build -d
```


4. Verify that the API is working:
```
curl http://localhost:5000/health
```
