import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './components/Layout';
import AdminLayout from './components/AdminLayout';
import LandingPage from './pages/LandingPage';
import MapPage from './pages/MapPage';
import IssueListPage from './pages/IssueListPage';
import IssueDetailPage from './pages/IssueDetailPage';
import ReportPage from './pages/ReportPage';
import HotspotsPage from './pages/HotspotsPage';
import AboutPage from './pages/AboutPage';
import AreaDetailPage from './pages/AreaDetailPage';
import AuthorityPublicPage from './pages/AuthorityPublicPage';
import SearchPage from './pages/SearchPage';
import AdminLoginPage from './pages/admin/AdminLoginPage';
import AdminDashboardPage from './pages/admin/AdminDashboardPage';
import ModerationQueuePage from './pages/admin/ModerationQueuePage';
import AdminIssueManagementPage from './pages/admin/AdminIssueManagementPage';
import AdminAuthorityPage from './pages/admin/AdminAuthorityPage';
import AdminAnalyticsPage from './pages/admin/AdminAnalyticsPage';
import AdminUserManagementPage from './pages/admin/AdminUserManagementPage';
import AdminAuditLogPage from './pages/admin/AdminAuditLogPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30000,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<LandingPage />} />
            <Route path="/map" element={<MapPage />} />
            <Route path="/issues" element={<IssueListPage />} />
            <Route path="/issues/:id" element={<IssueDetailPage />} />
            <Route path="/report" element={<ReportPage />} />
            <Route path="/hotspots" element={<HotspotsPage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/areas/:id" element={<AreaDetailPage />} />
            <Route path="/authorities/:id" element={<AuthorityPublicPage />} />
            <Route path="/search" element={<SearchPage />} />
          </Route>
          {/* Admin routes */}
          <Route path="/admin/login" element={<AdminLoginPage />} />
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<AdminDashboardPage />} />
            <Route path="moderation" element={<ModerationQueuePage />} />
            <Route path="issues" element={<AdminIssueManagementPage />} />
            <Route path="authorities" element={<AdminAuthorityPage />} />
            <Route path="analytics" element={<AdminAnalyticsPage />} />
            <Route path="users" element={<AdminUserManagementPage />} />
            <Route path="audit" element={<AdminAuditLogPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
