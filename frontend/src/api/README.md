# API Client

This folder is the checked-in frontend client surface for the current backend OpenAPI contract.

## Regenerate

1. Start the backend from `backend`.
2. Save the schema to `frontend/openapi.json`.
3. Run:

```powershell
npx openapi-typescript-codegen --input ./openapi.json --output ./src/api
```

The current files mirror the backend routes directly so frontend work can proceed before automated code generation is wired in.
