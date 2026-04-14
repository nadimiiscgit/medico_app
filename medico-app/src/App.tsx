import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Home } from './pages/Home';
import { Quiz } from './pages/Quiz';
import { PracticeTest } from './pages/PracticeTest';
import { Bookmarks } from './pages/Bookmarks';
import { Analytics } from './pages/Analytics';
import { Settings } from './pages/Settings';
import { Flashcard } from './pages/Flashcard';
import { Notes } from './pages/Notes';
import { Revision } from './pages/Revision';
import { useTheme } from './hooks/useTheme';

function App() {
  useTheme(); // Applies dark/light class to <html> on mount
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/quiz" element={<Quiz />} />
          <Route path="/practice" element={<PracticeTest />} />
          <Route path="/bookmarks" element={<Bookmarks />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/flashcard" element={<Flashcard />} />
          <Route path="/notes" element={<Notes />} />
          <Route path="/revision" element={<Revision />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
