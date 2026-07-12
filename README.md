# Route Optimization Platform

> Vehicle Routing Problem with Time Windows and Capacity Constraints (CVRPTW)

## Live Demo & Access

You can access the deployed version of the platform directly via Swagger UI:
**[http://139.100.207.201:5000/docs/](http://139.100.207.201:5000/docs/)** 

## Description

A logistics optimization system that solves the CVRPTW problem -
efficient routing of vehicles considering time windows and load capacity.

<img width="1910" height="850" alt="image" src="https://github.com/user-attachments/assets/cf2aeb63-0529-4ed6-a5a4-00ae16b23acb" />


## Documentation

- [Hosted Documentation Site](https://iu-students.github.io/route-optimization-platform/)
- [Customer Handover Guide](docs/customer-handover.md)
- [Development Process & Workflow](docs/development-process.md)
- [Architecture Documentation](docs/architecture/README.md)
- [Quality Requirements](docs/quality-requirements.md)
- [Testing Strategy & CI](docs/testing.md)
- [Product Roadmap](docs/roadmap.md)
- [Definition of Done](docs/definition-of-done.md)
- [User Acceptance Tests](docs/user-acceptance-tests.md)

## Contributing & Agents

- [Contributing Guide](CONTRIBUTING.md)
- [Agent Guide (AGENTS.md)](AGENTS.md)

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
curl http://localhost:5002/health
```

## Swagger UI

After starting the application, open `http://localhost:5000/docs` in your browser to access Swagger UI.

## API Version

Use the dropdown at the top of Swagger UI to switch between MVP versions. Current active version: **v2.2**

## Available Endpoints

- **POST /solve** - Start route optimization calculation.
- **GET /solution** - Get the computed optimal route after `/solve` completes.
- **GET /metrics** - Get cost breakdown statistics for the last completed solution.
- **GET /history** — List past calculations with summary metadata.
- **GET /history/{id}** — Get full calculation details including input/output files.
- **POST /validate** - Validate input JSON without solving.
- **GET /health** - Check server status.

## Authentication

All endpoints except `/health` require API key authentication. Include in request headers:
`X-API-Key: your-api-key`

The API key is set in the `.env` file.

## Known Limitations

- MVPv3 is currently under active development and not yet deployed to production. Some features may be unavailable until the next release.
- Solver Performance: The CP-SAT solver pipeline (MVPv2.2) achieves optimal results on 9 out of 10 standard test instances. Instance i4 remains challenging due to tight time windows and high vehicle/loader cost weights. We continue to work on improving performance for this edge case.

For detailed troubleshooting guidance and complete support documentation, please refer to our [Customer Handover Documentation](docs/customer-handover.md).


## Weekly reports

- [Week 2](reports/week2/README.md)
- [Week 3](reports/week3/README.md)
- [Week 4](reports/week4/README.md)
- [Week 5](reports/week5/README.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
