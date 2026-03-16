# mowen web frontend

React/TypeScript single-page application for the mowen authorship attribution
toolkit. Served statically by the FastAPI backend (`mowen-server`).

## Tech stack

- React 19 + TypeScript 5.9
- Vite 8 (build tool)
- React Router 7 (client-side routing)
- TanStack React Query (data fetching)
- Zustand (state management)

## Development

```bash
cd web/
npm install
npm run dev        # dev server with HMR at http://localhost:5173
```

The dev server proxies API requests to the backend. Start the backend first:

```bash
# In a separate terminal
pip install -e ../core/ -e ../server/
mowen-server
```

## Build

```bash
npm run build      # outputs to dist/
```

The production build is served by the FastAPI backend from `web/dist/`.

## Pages

| Route | Page | Purpose |
|-------|------|---------|
| `/` | Dashboard | Overview |
| `/documents` | Documents | Upload and manage documents |
| `/corpora` | Corpora | Create document collections |
| `/experiments/new` | Experiment Builder | Configure and submit experiments |
| `/experiments/:id/results` | Results | View attribution results |
