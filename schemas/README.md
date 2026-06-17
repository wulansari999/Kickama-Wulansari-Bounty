# JSON Schemas

This directory contains JSON Schema definitions for existing JSON data structures used by Zeroeye/Tent of Trials.

## Market Gateway API Error Response

- Schema: [`api-error.schema.json`](api-error.schema.json)
- Source data structure: `APIError` in [`market/gateway/api.go`](../market/gateway/api.go)
- JSON shape described: gateway error responses emitted by `writeJSON(...)`, including `code`, `message`, optional `request_id`, and optional `details`.
- Note: the Go field `StatusCode int` has `json:"-"`, so HTTP status is not part of the serialized payload and is rejected by this schema.

Example payloads live under [`examples/api-error/`](examples/api-error/):

- `valid-basic.json` — valid minimal error response.
- `valid-with-details.json` — valid response with a request ID and details object.
- `invalid-status-code.json` — invalid response because it includes the non-serialized `status_code` field.

Validate the examples locally with:

```sh
python3 -m pip install jsonschema
python3 schemas/validate_examples.py
```
