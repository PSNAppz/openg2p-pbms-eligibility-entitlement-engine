# OpenG2P Background Task API

This service provides a FastAPI-based HTTP API for managing background processing tasks in the OpenG2P workflow.

## Features

- Exposes endpoints to trigger and monitor background jobs for eligibility, entitlement, and disbursement processes.
- Integrates with Celery beat producers and workers for task orchestration.
- Includes a health check endpoint via the `PingInitializer`.

## Structure

- **main.py**: Entry point. Initializes the FastAPI app and health check.
- **app/**: Contains the application logic and API route definitions
