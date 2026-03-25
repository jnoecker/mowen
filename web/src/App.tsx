import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import PageLayout from './components/layout/PageLayout';

// Route-level code splitting — each page loaded on demand
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const DocumentsPage = lazy(() => import('./pages/DocumentsPage'));
const CorporaPage = lazy(() => import('./pages/CorporaPage'));
const ExperimentsListPage = lazy(() => import('./pages/ExperimentsListPage'));
const ExperimentBuilderPage = lazy(() => import('./pages/ExperimentBuilderPage'));
const ResultsPage = lazy(() => import('./pages/ResultsPage'));

function PageLoader() {
  return (
    <div style={{ padding: '2rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
      Loading…
    </div>
  );
}

function NotFoundPage() {
  return (
    <div>
      <h1>Page Not Found</h1>
      <p className="muted" style={{ marginBottom: '1rem' }}>
        This path leads nowhere — perhaps the author intended a different route.
      </p>
      <Link to="/dashboard">Return to Dashboard</Link>
    </div>
  );
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route element={<PageLayout />}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="documents" element={<DocumentsPage />} />
              <Route path="corpora" element={<CorporaPage />} />
              <Route path="experiments" element={<ExperimentsListPage />} />
              <Route path="experiments/new" element={<ExperimentBuilderPage />} />
              <Route path="experiments/:id/results" element={<ResultsPage />} />
              <Route path="*" element={<NotFoundPage />} />
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
