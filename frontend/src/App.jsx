import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AdminLayout from './components/layout/AdminLayout';
import { DashboardPage } from './pages/DashboardPage';
import { UsersPage } from './pages/UsersPage';
import { TaxonomiesPage } from './pages/content/TaxonomiesPage';
import { TagsPage } from './pages/content/TagsPage';
import { SuggestionsPage } from './pages/content/SuggestionsPage';
import { ResearchPage } from './pages/ResearchPage';
import { WriterPage } from './pages/WriterPage';
import { MediaPage } from './pages/MediaPage';
import { SocialAccountsPage } from './pages/social/AccountsPage';
import { SocialPostsPage } from './pages/social/PostsPage';
import { HashtagsPage } from './pages/social/HashtagsPage';
import { TranslationsPage } from './pages/TranslationsPage';

const App = () => {
  return (
    <BrowserRouter>
      <AdminLayout>
        <Routes>
          {/* Default redirect to dashboard */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          {/* Main dashboard */}
          <Route path="/dashboard" element={<DashboardPage />} />

          {/* Users management */}
          <Route path="/users" element={<UsersPage />} />

          {/* Content management */}
          <Route path="/content/taxonomies" element={<TaxonomiesPage />} />
          <Route path="/content/tags" element={<TagsPage />} />
          <Route path="/content/suggestions" element={<SuggestionsPage />} />

          {/* Research */}
          <Route path="/research" element={<ResearchPage />} />

          {/* Writer */}
          <Route path="/writer" element={<WriterPage />} />

          {/* Media */}
          <Route path="/media" element={<MediaPage />} />

          {/* Social Media */}
          <Route path="/social/accounts" element={<SocialAccountsPage />} />
          <Route path="/social/posts" element={<SocialPostsPage />} />
          <Route path="/social/hashtags" element={<HashtagsPage />} />

          {/* Translations */}
          <Route path="/translations" element={<TranslationsPage />} />

          {/* Catch-all redirect to dashboard */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AdminLayout>
    </BrowserRouter>
  );
};

export default App;