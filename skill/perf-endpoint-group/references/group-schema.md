# Group JSON schema

```json
{
  "name": "read",                       // folder/label prefix of the run
  "description": "...",
  "csv": [{"file": "data/products.csv", "vars": "product_id,keyword,quantity,price,pname"}],
  "setup": [ <step> ],                  // optional: runs ONCE per virtual user (e.g. login for a token)
  "steps":  [ <step> ],                 // runs every iteration, in order
  "slo": {"p95_ms": 75, "error_pct": 0.1},
  "think_ms": [500, 1500]               // uniform random pause before each request
}
```

Step fields:

| Field | Required | Meaning |
|---|---|---|
| `label` | yes | Sampler name in the JTL; keep it unique (`R1 Products`) |
| `method`, `path` | yes | HTTP method and path; JMeter variables allowed (`/api/products/${product_id}`) |
| `expect` | yes | Regex for the status code that means success: `"200"`, `"401\|403"` |
| `body` | no | JSON object (serialized for you) or raw string (use a string when values must be unquoted numbers from CSV) |
| `auth` | no | `true` adds `Authorization: Bearer ${token}` |
| `extract` | no | `{"var": "$.json.path"}`, e.g. `{"token": "$.token"}` |
| `percent` | no | Run this step only in N% of iterations (ThroughputController) |
| `slo` | no | `false` = report it but do not gate it (setup, negative tests) |
| `slo_p95_ms` | no | Per-step p95 limit that overrides the group default |

CSV paths are relative to the project root. The generator turns them into absolute paths, because JMeter resolves relative paths against the .jmx folder.
