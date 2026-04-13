import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Home } from './pages/Home';
import { Browse } from './pages/Browse';
import { Quiz } from './pages/Quiz';
import { PracticeTest } from './pages/PracticeTest';
import { Bookmarks } from './pages/Bookmarks';
import { Analytics } from './pages/Analytics';
import { Settings } from './pages/Settings';
import { useTheme } from './hooks/useTheme';

function App() {
  useTheme(); // Applies dark/light class to <html> on mount
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/browse" element={<Browse />} />
          <Route path="/quiz" element={<Quiz />} />
          <Route path="/practice" element={<PracticeTest />} />
          <Route path="/bookmarks" element={<Bookmarks />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
