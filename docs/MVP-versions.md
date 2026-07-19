# MVP Versions

## MVPv3 - Multi-Start + LNS

| | |
|---|---|
| **Port** | `5003` (internal) -> `5003` (host) |
| **Status** | **Active production version** |
| **Solver** | CP-SAT |
| **Architecture** | `Web/` + `CP-SAT/` + `Shared/` |

**Characteristics:**
- **Multi-start** - multiple independent solve cycles with random seeds, best result selected
- **LNS (Large Neighborhood Search)** - polish phase after multi-start: local search + perturbation + loader re-solve until deadline
- **OR-Tools** - optional route seed generator for the pool
- **Dual-mode feedback** - conservative and aggressive burden estimates both tested, best picked
- **`shift_mode`** - departure calculation mode: `earliest` (earliest possible) or `min_duration` (minimum shift duration)
- **`optional_penalty_factor`** - internal penalty multiplier for skipping optional orders
- **Inter-route local search** - 2-opt-like improvement between routes after consolidation
- **Scaled budgets** - pool timeouts scale by instance size (small/medium/large)
- **All v2.2 endpoints**

**Endpoints:** `POST /solve`, `GET /solution`, `POST /validate`, `GET /metrics`, `GET /history`, `GET /history/{id}`, `GET /health`

---

## MVPv2.2 - Current production version (with calculation history)

| | |
|---|---|
| **Port** | `5022` (internal) -> `5022` (host) |
| **Status** | **Historic** |
| **Solver** | CP-SAT (Pipeline A) + PyVRP (Pipeline B, CLI only) |
| **Architecture** | `Web/` + `CP-SAT/` + `PyVRP/` + `Shared/` |

**Characteristics:**
- **Calculation history** - SQLite-backed persistent storage (`GET /history`, `GET /history/{id}`), each `/solve` request gets a `calculation_id`
- **Pool reuse** - pool is not regenerated during feedback iteration, only CP-SAT re-solves
- **Consolidation + multi-trip merging** - post-processing of routes
- **Stage reporting + metrics + feedback loop** 

**Endpoints:** `POST /solve`, `GET /solution`, `POST /validate`, `GET /metrics`, `GET /history`, `GET /history/{id}`, `GET /health`

---

## MVPv2 - Modular architecture + metrics

| | |
|---|---|
| **Port** | `5002` (internal) -> `5002` (host) |
| **Status** | Historic |
| **Solver** | CP-SAT (Pipeline A) + PyVRP (Pipeline B, CLI only) |
| **Architecture** | `Web/` + `CP-SAT/` + `PyVRP/` + `Shared/` |

**Characteristics:**
- **First modular architecture** - separation into `Web/`, `CP-SAT/`, `PyVRP/`, `Shared/`
- **`GET /metrics`** - returns detailed cost breakdown (fuel_cost, vehicle_salaries, loader_salaries, penalties, counts)
- **`POST /validate`** - validate input data without solving
- **Feedback loop** - two-phase solving: first run -> identify unprofitable optional orders -> re-solve without them
- **Stage reporting** - solver reports progress stages ("solving_vehicles", "solving_loaders", etc.) via `on_stage` callback
- **Statistics** embedded in solution JSON

**Endpoints:** `POST /solve`, `GET /solution`, `POST /validate`, `GET /metrics`, `GET /health`

---

## MVPv1.2 - Validation + reduced solver budget

| | |
|---|---|
| **Port** | `5011` (internal) -> `5011` (host) |
| **Status** | Historic |
| **Solver** | PyVRP (vehicle routes) + CP-SAT (heuristic orchestration) + custom loader routing |
| **Architecture** | Flat files |

**Characteristics:**
- **Input validation** (`validator.py`) - checks types, ranges, required fields before solving
- **Improved loader routing** - iterative removal of unprofitable optional points using cost/benefit analysis
- **Loader model** includes `mandatory` flag, `loader_salary`/`loader_work` cost weighting

**Endpoints:** `POST /solve`, `GET /solution`, `GET /health`

---

## MVPv1 - First functional solver

| | |
|---|---|
| **Port** | `5001` (internal) -> `5001` (host) |
| **Status** | Historic |
| **Solver** | PyVRP (vehicle routes) + CP-SAT (heuristic orchestration) + custom loader routing |
| **Architecture** | Flat files |

**Characteristics:**
- **First release with actual optimization** 
- **PyVRP** for vehicle routing 
- **CP-SAT** for heuristic orchestration (Clarke-Wright savings + insertion)
- **Custom greedy loader routing** 
- **Post-solution verification** (`verifier.py`) - shift times, time windows, truck capacity

**Endpoints:** `POST /solve`, `GET /solution`, `GET /health`

---

## MVPv0 - Mock prototype

| | |
|---|---|
| **Port** | `5000` (internal) -> `5000` (host) |
| **Status** | Historic / archived |
| **Solver** | **None** - returns a hardcoded JSON response |
| **Architecture** | Single file (`app.py`) |

**Characteristics:**
- **Mock endpoint** - all `POST /solve` requests return the same response from `response.json`
- **Swagger UI** - built-in at `/docs`, spec at `/openapi.yaml`
- **API Key** - `X-API-Key` header check
- **No optimization**, no validation

**Endpoints:** `POST /solve`, `GET /docs`, `GET /openapi.yaml`, `GET /health`
