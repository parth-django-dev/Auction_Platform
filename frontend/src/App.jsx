import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { AuthModal } from './components/AuthModal';
import { CreateAuctionModal } from './components/CreateAuctionModal';
import { AuctionCatalog } from './pages/AuctionCatalog';
import { AuctionArena } from './pages/AuctionArena';
import { Dashboard } from './pages/Dashboard';
import { api } from './api/client';

export function AppContent() {
  const navigate = useNavigate();
  const location = useLocation();

  const [activeCount, setActiveCount] = useState(0);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [catalogRefreshKey, setCatalogRefreshKey] = useState(0);

  const fetchCount = () => {
    api.getActiveAuctions()
      .then((data) => {
        const list = data.AuctionList || [];
        const liveCount = list.filter((a) => a.is_live).length;
        setActiveCount(liveCount);
      })
      .catch((err) => console.warn('Could not fetch count:', err));
  };

  useEffect(() => {
    fetchCount();
  }, [catalogRefreshKey]);

  const handleSelectAuction = (id) => {
    if (!id) {
      navigate('/');
      return;
    }
    navigate(`/auction/${id}`);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleNavigate = (targetView) => {
    if (targetView === 'dashboard') {
      navigate('/dashboard');
    } else {
      navigate('/');
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleItemCreated = (newItem) => {
    setCatalogRefreshKey((k) => k + 1);
    if (newItem?.id) {
      navigate(`/auction/${newItem.id}`);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const currentView = location.pathname.startsWith('/auction')
    ? 'arena'
    : location.pathname === '/dashboard'
    ? 'dashboard'
    : 'catalog';

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        onNavigate={handleNavigate}
        currentView={currentView}
        activeAuctionCount={activeCount}
        onOpenCreateModal={() => setIsCreateModalOpen(true)}
      />

      <main style={{ flex: 1 }}>
        <Routes>
          <Route
            path="/"
            element={
              <AuctionCatalog
                key={catalogRefreshKey}
                onSelectAuction={handleSelectAuction}
                onOpenCreateModal={() => setIsCreateModalOpen(true)}
              />
            }
          />
          <Route
            path="/auction/:id"
            element={<AuctionArena onBack={() => handleNavigate('catalog')} />}
          />
          <Route
            path="/dashboard"
            element={
              <Dashboard
                onSelectAuction={handleSelectAuction}
                onOpenCreateModal={() => setIsCreateModalOpen(true)}
              />
            }
          />
          {/* Fallback to catalog */}
          <Route
            path="*"
            element={
              <AuctionCatalog
                key={catalogRefreshKey}
                onSelectAuction={handleSelectAuction}
                onOpenCreateModal={() => setIsCreateModalOpen(true)}
              />
            }
          />
        </Routes>
      </main>

      <AuthModal />

      <CreateAuctionModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onItemCreated={handleItemCreated}
      />

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid var(--border-dim)',
        padding: '30px 24px',
        textAlign: 'center',
        color: 'var(--text-dim)',
        fontSize: '0.85rem',
      }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto', display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '16px' }}>
          <div>
            <strong>LiveBid</strong> — High Concurrency Real-Time Auction Platform
          </div>
          <div>
            Powered by Django Channels, Daphne ASGI, Redis, and React
          </div>
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </AuthProvider>
  );
}
