# Development notes

Contributor conventions, lint/test commands, and PR rules live in
[AGENTS.md](../AGENTS.md) and the README Development section.

## Regenerating protobuf stubs

```bash
python -m grpc_tools.protoc -Isrc/pybravia_connect/proto \
  --python_out=src/pybravia_connect/proto \
  --grpc_python_out=src/pybravia_connect/proto \
  src/pybravia_connect/proto/bravia_control.proto
```

Then re-apply two manual patches:

1. Make the `pb2_grpc` import relative: `from . import bravia_control_pb2`.
2. Register the descriptor in a **private** pool, not the global `Default()` one
   (`_pool = DescriptorPool()` / `DESCRIPTOR = _pool.AddSerializedFile(...)`).
   This avoids symbol collisions when co-installed with integrations that still
   vendor their own stubs.
