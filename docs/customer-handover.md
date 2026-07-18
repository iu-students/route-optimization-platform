# Customer Handover Documentation

**Product:** Route Optimization Platform

**Version:** MVPv3, release v1.0.0

**Date:** 2026-07-18

---

## 1. Current Product Status and Handover Scope

### 1.1 Product Status

- **Current State:** **MVPv3 is live and operational** in production. This is the final course version of the product.
- **Deployment Date:** 2026-07-18
- **Health/Performance:** All services are operational. Each endpoint returns an HTTP response within 2.0 seconds.

### 1.2 Handover Scope
This handover covers the transfer of operational ownership and knowledge for the following components:

- **Repository:** https://github.com/iu-students/route-optimization-platform
- **Core Service:** Route Optimization API Service
- **Database:** SQLite Database (file: `root/data/history.db`)
- **Deployment Targets:** Docker and Docker Compose
- **Transferred Ownership:**
    - User rights to use the API service
    - Administrator rights to the repository
- **Retained by Team:** 
    - Administrator rights to the repository

---

## 2. Access and Usage

### 2.1 How the Customer Accesses the Product

- **URL:** Swagger UI available at http://139.100.207.201:5000/docs
- **Authentication:** All endpoints except `/health` require API key authentication.
  - **Header:** `X-API-Key: your-api-key`
  - API key is configured in the `.env` file.

### 2.2 Required Customer Access

To fully operate the product, the customer must have access to:

- **GitHub Repository:** Admin access
- **API Service:** User access
- **Database:** Admin access
- **CI/CD Pipeline:** View access to GitHub Actions

---

## 3. Installation Instrustions

Follow  these steps to set up the product for the first time:

### 3.1 Initial Setup for the Customer

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/iu-students/route-optimization-platform.git
   cd route-optimization-platform
   ```

2. **Create Environment Configuration:**

   ```bash
   cp .env.example .env
   ```

   Update the `.env` file with the required values (see Section 4 for details).

3. **Start with Docker Compose:**

   ```bash
   docker compose up --build -d
   ```

   This command builds the Docker images and starts all required services in detached mode.

4. **Verify Installation:**

   ```bash
   curl http://localhost:5002/health
   ```

   Expected response: `{"status":"ok"}`.

5. **Access API Documentation:**

   Open `http://localhost:5000/docs` in your browser to access Swagger UI.

### 3.2 API Version Management

Use the dropdown at the top of Swagger UI to switch between MVP versions. **Current active version: v3**

Follow https://github.com/iu-students/route-optimization-platform/blob/main/README.md for detailed instructions.

---

## 4. Configuration and Secrets Management

### 4.1 Critical Environment Variables

The following environment variables are essential for operation. **Do not expose these values in code.**

| Variable Name | Description | How to Obtain |
| :--- | :--- | :--- |
| `API_KEY` | The authentication key required for all API requests. | Set in `.env` file. |
| `FLASK_HOST` | Network interface the Flask server binds to. | Default: `127.0.0.1` (local only). Use `0.0.0.0` to expose externally. |
| `FLASK_DEBUG` | Enables or disables Flask debug mode. | Set to `false` in production. Use `true` only for development. |

### 4.2 Secrets Handling Steps

#### Local Development

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Generate an `API_KEY`.
3. Edit `.env` with your values.
4. **Never commit `.env` to version control** (ensure it's in `.gitignore`).

#### Production Environment
- Use a secrets manager (recommended):
  - **Docker:** Use `--env-file` with restricted permissions

---

## 5. Operational Notes and Maintenance

- **Health Check:** `GET /health` - Use for monitoring service availability.
- **API Documentation:** Swagger UI at `/docs` - Interactive API exploration.
- **Logging:** Docker logs

**Docker Commands:**

```bash
# View logs
docker compose logs -f

# Stop services
docker compose down

# Restart services
docker compose restart
```

---

## 6. Troubleshooting and Support Guidance

### 6.1 Common Issues

| Symptom | Likely Cause | Resolution guide |
| :--- | :--- | :--- |
| 401 Unauthorized | Missing or invalid API key | Ensure `X-API-Key` header is included and matches the value in `.env` |
| 400 Bad Request | Invalid input format | Validate input using `POST /validate` first |
| 500 Internal Server Error | Database connection issue or solver failure | Check logs: `docker compose logs -f` |

### 6.2 Support Escalation

| Level | Contact | Expected Respond Time |
| :--- | :--- | :--- |
| **Development Team** | See Team contacts in [README.md](https://github.com/iu-students/route-optimization-platform/blob/main/README.md) | Within 24 hours |

---

## 7. Known Limitations, Unfinished Areas, and Risks

- **Risk 1:** High-load production environments may require migration from SQLite to a more performant database.
- **Risk 2:** If the API key is lost or compromised, it must be updated in the .env file and services restarted.
- **Limitation 1:** The optimization algorithms are based on heuristics and metaheuristics (including CP-SAT). As a result, **the solver may produce different solutions for identical inputs** across different runs. This is expected behavior for heuristic approaches, which balance solution quality against computational speed.

---

## 8. Handover Status and Remaining Actions

### 8.1 Current Handover Status
**Level Reached:** 

- [ ] **Ready for independent use**  
    *Explanation: The documentation is complete, and the system is stable. The customer is trained and has the necessary access to start using it independently.*

- [ ] **Independently used by customer**  
    *Explanation: The customer has been operating the product independently in a staging environment for 2 weeks and is preparing for the production cutover.*

- [x] **Deployed or operated on customer side**  
    *Explanation: The system is live in the customer's production environment. The handover is complete for this phase, with monitoring in a hyper-care period.*

### 8.2 Customer Confirmation Status

- [x] Accepted

- [ ] Accepted with follow-up items

- [ ] Not yet accepted

Explanation: The customer has confirmed that the documentation and product are ready for use and has confirmed successful deployment.


### 8.3 Remaining Actions

| Action Item | Blocker? | Status |
| :--- | :--- | :--- |
| Transfer repository administrator rights | Yes | Completed |
| Transfer API service access credentials | Yes | Completed |
| Implement MVPv3 | Yes | Completed |
| Improve algorithm performance to beat baseline on all 10/10 test instances | Yes | Completed |
| Post-handover monitoring and support | No | Active |

All blocking items have been completed, so the transfer can be completed.

---

## 9. Main Entry Points for Documentation

| Name | Description | Link |
| :--- | :--- | :--- |
| **README.md** | Project overview and quick start guide | https://github.com/iu-students/route-optimization-platform/blob/main/README.md |
| **Swagger UI** | Interactive API documentation | http://139.100.207.201:5000/docs |
| Route Optimization Platform - Docs | Testing, architecture, user stories and team-dependent variables documentation | https://iu-students.github.io/route-optimization-platform/ |

---

## 10. Summary of Documentation Sufficiency

**Is the current documentation set sufficient for the reached handover level?**

- [x] Yes, all critical operational and troubleshooting information is documented.
- [ ] No, the following gaps exist: [List specific missing documents or outdated sections].

**Support Arrangement Post-Handover:**

- The development team will provide post-handover support if necessary. See Team contacts in [README.md](https://github.com/iu-students/route-optimization-platform/blob/main/README.md).

---
