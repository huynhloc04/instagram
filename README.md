# Flask API Service Starter

This is a minimal Flask API service starter based on [Google Cloud Run Quickstart](https://cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-service).

## Getting Started

Server should run automatically when starting a workspace. To run manually, run:
```sh
./devserver.sh
```

### Flask Database Migration

```bash
1, Init migration
    >> python -m flask --app app/main db init

2, Start migrating
    >> python -m flask --app app/main db migrate -m "message"

3, Upgrade
    >> python -m flask --app app/main db upgrade
```