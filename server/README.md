# mowen-server

FastAPI web server and React UI for [mowen](https://pypi.org/project/mowen/), the authorship attribution toolkit.

## Install

```bash
pip install mowen-server
```

This installs the `mowen-server` command, the core library, and all server dependencies.

## Usage

```bash
mowen-server
```

Open http://localhost:8000 for the web UI. API docs at http://localhost:8000/docs.

## Features

- Upload and manage documents (plain text, PDF, DOCX, HTML)
- Organize documents into corpora
- Import from 20 bundled sample corpora (Federalist Papers, Shakespeare, Homer, etc.)
- Build experiments with a step-by-step wizard and 16 stylometry presets
- View attribution results with performance metrics and score visualizations
- REST API with OpenAPI documentation

## Configuration

Environment variables (all prefixed `MOWEN_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `MOWEN_DATABASE_URL` | `sqlite:///{home}/.mowen/data.db` | Database connection |
| `MOWEN_UPLOAD_DIR` | `~/.mowen/documents` | Document storage path |
| `MOWEN_HOST` | `127.0.0.1` | Bind address |
| `MOWEN_PORT` | `8000` | Port |
| `MOWEN_CORS_ORIGINS` | `["*"]` | Allowed CORS origins |

## Docker

```bash
docker compose up
```

Serves the full app at http://localhost:8000 with data persisted in a Docker volume.

## Documentation

See the [mowen repository](https://github.com/jnoecker/mowen) for full documentation.

## License

MIT — Copyright 2026 John Noecker Jr.
