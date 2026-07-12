# Route Optimization Platform - MVP v0

## 1. Overview
MVP v0 provides an API for route operations. It can accept data in JSON format (distinguishes JSON format) and returns an example correct response containing routes for cargo and vehicles (for any request). The API conforms to the OpenAPI specification in `api/openapi.yaml`.

## 2. API Links
- **Swagger UI**: http://139.100.207.201:5000/docs/
- **API**: http://139.100.207.201:5000/
- **Health check**: http://139.100.207.201:5000/health/
- **Solver**: http://139.100.207.201:5000/solve/

## 3. Demo Video
https://drive.google.com/file/d/1xmlnW_k2o_Vc19OKTqINv9av96VN2rC5/view?usp=drive_link

## 4. Interface Prototype
The interface prototype is described in `api/openapi.yaml`. MVP v0 implements endpoints for route calculation and service health checking. The optimization and status endpoints return mock responses that conform to the schema from the prototype.

## 5. Mocks and Limitations

### Mocks
- The `/solve/` endpoint always returns the same example optimized route
- The server does not perform actual optimization calculations

### Limitations
- The server does not validate incoming requests - accepts any JSON
- Data is not persisted anywhere (in-memory, lost on restart)
- API key is required for authorization (passed in the `X-API-Key` header)
- No support for concurrent requests

## 6. Requirements
- Docker and Docker Compose

## 7. SETUP
https://github.com/iu-students/route-optimization-platform#setup-steps

## 8. Smoke Test Scenario

1. Open browser at http://139.100.207.201:5000/docs/  
   (Swagger UI page loads)

2. Execute `GET /health/`  
   HTTP 200, body `{"status": "ok"}`

3. Execute `POST /solve/` with any JSON body  
   HTTP 200, returns JSON with an example route
