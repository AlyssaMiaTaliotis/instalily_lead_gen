Run locally with: uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8080

Lead generation


curl -X POST http://127.0.0.1:8080/api/generate-leads \
-H "Content-Type: application/json" \
-d '{"target_industries": ["signage", "graphics"], "max_leads": 5, "min_company_size": "medium", "include_outreach": false}'



curl http://127.0.0.1:8080/api/task-status

curl http://127.0.0.1:8080/api/leads

curl http://127.0.0.1:8080/api/leads/lead_2_20250723_214750