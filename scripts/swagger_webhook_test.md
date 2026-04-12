# Swagger UI — Webhook Test Data

Open http://localhost:8000/docs, find `POST /webhook/github`, click **Try it out**.

## Headers

**x-github-event**
```
issues
```

**x-github-delivery**
```
518d6b60-540b-4105-a841-fb99c5de1714
```

**x-hub-signature-256**
```
sha256=1381594c412a652b8c5adef43da040c6049360f9f8bb988f7d9f0679ce28f968
```

## Request Body

```json
{"action":"opened","installation":{"id":99001},"repository":{"id":123456789,"full_name":"smoke-org/smoke-repo","private":false},"issue":{"number":101,"id":10101,"node_id":"I_dev_test","url":"https://api.github.com/repos/smoke-org/smoke-repo/issues/101","html_url":"https://github.com/smoke-org/smoke-repo/issues/101","title":"App crashes on login \u2014 null pointer exception","body":"Steps to reproduce: open the app and tap login. Traceback attached. This is a regression from v1.2.","labels":[],"user":{"login":"reporter"},"created_at":"2026-04-08T00:00:00Z","updated_at":"2026-04-08T00:00:00Z"},"sender":{"login":"reporter"}}
```

## Expected Response

```json
{"status": "queued", "delivery_id": "518d6b60-540b-4105-a841-fb99c5de1714"}
```

Sending the same request a second time returns:
```json
{"status": "duplicate", "delivery_id": "518d6b60-540b-4105-a841-fb99c5de1714"}
```

## Notes

- These values are tied to each other — do not mix headers from one signing with a different body.
- To send a fresh event, call `POST /dev/sign-webhook` again with a different `issue.number`
  and use the new values returned.
- The worker will classify this issue as `bug / P1` (title contains "crashes" and "null pointer")
  and assign it to `emmanuel` (seeded developer with `skills=["bug"]` and available capacity).
