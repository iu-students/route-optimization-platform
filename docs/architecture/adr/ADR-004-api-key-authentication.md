# ADR-004: API Key Authentication as the Sole Access Control Boundary

**Status:** Accepted

**Quality requirements addressed:** QR-002

## Context

The API exposes sensitive route data (order locations, time windows, volumes) and solver results over HTTP. Without access control, any party that discovers the service URL can read or submit route data. The team needed a lightweight authentication mechanism appropriate for a single-tenant, low-concurrency deployment where the primary consumer is one dispatcher or an integration script.

Options considered:
- Shared API key validated via HTTP header
- HTTP Basic Auth with a shared credential
- OAuth2 / token-based identity provider
- No authentication (open endpoint)

## Decision

Use a single shared API key validated via the `X-API-Key` request header at every protected endpoint (`POST /solve`, `GET /solution`, `GET /metrics`). The `/health` and `/validate` endpoints remain unauthenticated. The key is supplied through the `API_KEY` environment variable and checked inline by `require_api_key()` in `app.py` before each protected handler runs.

## Rationale

- Shared API key is the simplest mechanism that meets the confidentiality requirement: unauthenticated callers receive HTTP 401 before any business logic executes.
- No session state, token refresh, or user database needed - matches the single-tenant deployment model.
- The key is configurable via environment variable, keeping it out of the codebase and supporting per-deployment key rotation.
- OAuth2 would add infrastructure (authorization server, token validation) that the current deployment scale does not justify.

## Consequences

### Positive

- Every protected endpoint is guarded by a single consistent check - no endpoint can be added without authentication unless explicitly exempted.
- The `require_api_key()` call is a one-line decorator-equivalent in each handler, keeping the authentication surface easy to audit.

### Negative

- A shared key provides no audit trail per caller - all authenticated requests are indistinguishable.
- Key rotation requires updating the environment variable and restarting the container; no gradual key migration support.

### Tradeoffs

- Per-user authentication was not adopted: the product has a single dispatcher role, and adding user management would introduce complexity (registration, password storage, session management) without proportional benefit.
- The key is transmitted in plaintext in the `X-API-Key` header - production deployments should front the service with TLS termination.

## Links

- [QR-002: Route data confidentiality](../../quality-requirements.md#qr-002-route-data-confidentiality)
- [Deployment Diagram](../deployment-view/deployment-diagram.puml)
