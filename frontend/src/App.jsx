import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { LoginPage } from '@/pages/LoginPage';
import AdminLayout from '@/components/layout/AdminLayout';
import { DashboardPage } from '@/pages/DashboardPage';
import { UsersPage } from '@/pages/UsersPage';
import { TaxonomiesPage } from '@/pages/content/TaxonomiesPage';
import { TagsPage } from '@/pages/content/TagsPage';
import { SuggestionsPage } from '@/pages/content/SuggestionsPage';
import { ResearchPage } from '@/pages/ResearchPage';
import { WriterPage } from '@/pages/WriterPage';
import { MediaCandidatesPage } from '@/pages/media/MediaCandidatesPage';
import { MediaLibraryPage } from '@/pages/media/MediaLibraryPage';
import { MediaSuggestionsPage } from '@/pages/media/MediaSuggestionsPage.jsx';
import { SocialAccountsPage } from '@/pages/social/AccountsPage';
import { SocialPostsPage } from '@/pages/social/PostsPage';
import { HashtagsPage } from '@/pages/social/HashtagsPage';
import { TranslationsPage } from '@/pages/TranslationsPage';
import { Toaster } from "@/components/ui/use-toast"

const App = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public route */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected routes */}
          <Route element={
            <ProtectedRoute>
              <AdminLayout />
            </ProtectedRoute>
          }>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/users" element={<UsersPage />} />
            <Route path="/content/taxonomies" element={<TaxonomiesPage />} />
            <Route path="/content/tags" element={<TagsPage />} />
            <Route path="/content/suggestions" element={<SuggestionsPage />} />
            <Route path="/research" element={<ResearchPage />} />
            <Route path="/writer" element={<WriterPage />} />
            <Route path="/media/suggestions" element={<MediaSuggestionsPage />} />
            <Route path="/media/candidates" element={<MediaCandidatesPage />} />
            <Route path="/media/library" element={<MediaLibraryPage />} />
            <Route path="/social/accounts" element={<SocialAccountsPage />} />
            <Route path="/social/posts" element={<SocialPostsPage />} />
            <Route path="/social/hashtags" element={<HashtagsPage />} />
            <Route path="/translations" element={<TranslationsPage />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Route>
        </Routes>
        <Toaster />
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;