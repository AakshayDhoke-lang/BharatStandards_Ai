import { type ReactNode } from "react";
import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { LoaderCircle } from "lucide-react";
import { DashboardPage } from "@/components/is-guide/dashboard";
import { AnalyzePage } from "@/components/is-guide/analyze";
import { ResultsPage } from "@/components/is-guide/results";
import {
  AmendmentsPage, CertificationPage, CompliancePage, EvaluationPage, HistoryPage,
  IngestionPage, LoginPage, ProductsPage, RelationshipsPage, ReviewPage, SettingsPage,
  StandardDetailsPage, StandardsPage,
} from "@/components/is-guide/explorers";
import { SharedSourcesPage, SharedIngestionPage, SharedReviewPage, DataActivityPage, SystemDiagnosticsPage, SharedStandardsPage, SharedStandardDetailsPage, SharedProductsPage, SharedCategoriesPage, SharedRelationshipsPage, SharedCertificationPage, SharedAmendmentsPage } from "@/components/is-guide/data-management";
import { useAuth } from "@/contexts/AuthContext";

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading, firebaseConfigured } = useAuth();
  const location = useLocation();
  if (loading) return <div className="grid min-h-screen place-items-center bg-background"><LoaderCircle className="h-7 w-7 animate-spin text-primary"/></div>;
  if (!firebaseConfigured || !user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return <>{children}</>;
}

function PublicOnlyLogin() {
  const { user, loading } = useAuth();
  if (loading) return <div className="grid min-h-screen place-items-center bg-background"><LoaderCircle className="h-7 w-7 animate-spin text-primary"/></div>;
  return user ? <Navigate to="/" replace /> : <LoginPage />;
}

function NotFoundPage() {
  return (
    <div className="grid min-h-screen place-items-center bg-background px-4">
      <div className="max-w-md text-center">
        <p className="text-7xl font-bold text-navy">404</p>
        <h1 className="mt-4 text-xl font-semibold">Page not found</h1>
        <p className="mt-2 text-sm text-muted-foreground">The requested BharatStandards AI page does not exist.</p>
        <Link to="/" className="mt-6 inline-flex rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">Go to Dashboard</Link>
      </div>
    </div>
  );
}

const protect = (element: ReactNode) => <ProtectedRoute>{element}</ProtectedRoute>;

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<PublicOnlyLogin />} />
      <Route path="/" element={protect(<DashboardPage />)} />
      <Route path="/analyze" element={protect(<AnalyzePage />)} />
      <Route path="/results" element={protect(<ResultsPage />)} />
      <Route path="/standards" element={protect(<SharedStandardsPage />)} />
      <Route path="/standards/:standardId" element={protect(<SharedStandardDetailsPage />)} />
      <Route path="/products" element={protect(<SharedProductsPage />)} />
      <Route path="/relationships" element={protect(<SharedRelationshipsPage />)} />
      <Route path="/certification" element={protect(<SharedCertificationPage />)} />
      <Route path="/amendments" element={protect(<SharedAmendmentsPage />)} />
      <Route path="/compliance" element={protect(<CompliancePage />)} />
      <Route path="/history" element={protect(<HistoryPage />)} />
      <Route path="/evaluation" element={protect(<EvaluationPage />)} />
      <Route path="/categories" element={protect(<SharedCategoriesPage />)} />
      <Route path="/sources" element={protect(<SharedSourcesPage />)} />
      <Route path="/ingestion" element={protect(<SharedIngestionPage />)} />
      <Route path="/review" element={protect(<SharedReviewPage />)} />
      <Route path="/settings" element={protect(<SettingsPage />)} />
      <Route path="/activity" element={protect(<DataActivityPage />)} />
      <Route path="/diagnostics" element={protect(<SystemDiagnosticsPage />)} />
      <Route path="/dashboard" element={<Navigate to="/" replace />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
