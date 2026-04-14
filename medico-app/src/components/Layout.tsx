import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { cn } from '../lib/utils';
import {
  HomeIcon,
  ClockIcon,
  BookOpenIcon,
  BookmarkIcon,
  BarChart3Icon,
  SettingsIcon,
  BrainIcon,
  LayersIcon,
  PencilIcon,
  FileTextIcon,
  GridIcon,
  XIcon,
} from 'lucide-react';

const NAV_ITEMS = [
  { to: '/', icon: HomeIcon, label: 'Home' },
  { to: '/practice', icon: ClockIcon, label: 'Practice Test' },
  { to: '/quiz', icon: BookOpenIcon, label: 'Quiz Mode' },
  { to: '/flashcard', icon: LayersIcon, label: 'Flashcards' },
  { to: '/revision', icon: FileTextIcon, label: 'Revision' },
  { to: '/bookmarks', icon: BookmarkIcon, label: 'Bookmarks' },
  { to: '/notes', icon: PencilIcon, label: 'My Notes' },
  { to: '/analytics', icon: BarChart3Icon, label: 'Analytics' },
  { to: '/settings', icon: SettingsIcon, label: 'Settings' },
];

// First 4 always visible in bottom bar; rest go into the "More" drawer
const BOTTOM_NAV = NAV_ITEMS.slice(0, 4);
const MORE_NAV = NAV_ITEMS.slice(4);

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const [showMore, setShowMore] = useState(false);

  // Is the current route one of the "more" items? If so, highlight the More button.
  const isMoreActive = MORE_NAV.some((item) =>
    item.to === '/'
      ? location.pathname === '/'
      : location.pathname.startsWith(item.to)
  );

  return (
    <div className="flex min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* ── Desktop sidebar ─────────────────────────────────────── */}
      <aside className="hidden md:flex w-60 flex-col bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 fixed h-full z-10">
        {/* Logo */}
        <div className="flex items-center gap-3 px-5 py-5 border-b border-gray-100 dark:border-gray-800">
          <div className="w-9 h-9 bg-blue-600 rounded-xl flex items-center justify-center flex-shrink-0">
            <BrainIcon className="w-5 h-5 text-white" />
          </div>
          <div>
            <p className="font-bold text-gray-900 dark:text-gray-100 text-sm leading-tight">NEET PG</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Question Bank</p>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
                  isActive
                    ? 'bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-400'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-100'
                )
              }
            >
              {({ isActive }) => (
                <>
                  <Icon
                    className={cn('flex-shrink-0', isActive ? 'text-blue-600 dark:text-blue-400' : 'text-gray-400 dark:text-gray-500')}
                    style={{ width: '18px', height: '18px' }}
                  />
                  {label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-gray-100 dark:border-gray-800">
          <p className="text-xs text-gray-400 dark:text-gray-600">NEET PG 2012–2024</p>
          <p className="text-xs text-gray-400 dark:text-gray-600">10,368 Questions</p>
        </div>
      </aside>

      {/* ── Mobile top bar ───────────────────────────────────────── */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-20 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-blue-600 rounded-lg flex items-center justify-center">
            <BrainIcon className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-gray-900 dark:text-gray-100 text-sm">NEET PG QB</span>
        </div>
      </div>

      {/* ── Mobile bottom nav (4 items + More) ──────────────────── */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-20 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 flex">
        {BOTTOM_NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              cn(
                'flex-1 flex flex-col items-center gap-0.5 py-2 text-xs font-medium transition-colors',
                isActive ? 'text-blue-600' : 'text-gray-500 dark:text-gray-400'
              )
            }
          >
            {({ isActive }) => (
              <>
                <Icon className={cn('w-5 h-5', isActive ? 'text-blue-600' : 'text-gray-400 dark:text-gray-500')} />
                <span className="text-[10px]">{label.split(' ')[0]}</span>
              </>
            )}
          </NavLink>
        ))}

        {/* More button */}
        <button
          onClick={() => setShowMore(true)}
          className={cn(
            'flex-1 flex flex-col items-center gap-0.5 py-2 text-xs font-medium transition-colors',
            isMoreActive ? 'text-blue-600' : 'text-gray-500 dark:text-gray-400'
          )}
        >
          <GridIcon className={cn('w-5 h-5', isMoreActive ? 'text-blue-600' : 'text-gray-400 dark:text-gray-500')} />
          <span className="text-[10px]">More</span>
        </button>
      </nav>

      {/* ── More drawer (slide-up) ───────────────────────────────── */}
      {showMore && (
        <>
          {/* Backdrop */}
          <div
            className="md:hidden fixed inset-0 z-30 bg-black/40 backdrop-blur-sm"
            onClick={() => setShowMore(false)}
          />

          {/* Sheet */}
          <div className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white dark:bg-gray-900 rounded-t-2xl border-t border-gray-200 dark:border-gray-800 shadow-xl">
            {/* Handle + header */}
            <div className="flex items-center justify-between px-5 pt-4 pb-3 border-b border-gray-100 dark:border-gray-800">
              <div className="w-10 h-1 rounded-full bg-gray-300 dark:bg-gray-700 mx-auto absolute left-1/2 -translate-x-1/2 top-2" />
              <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">All Pages</span>
              <button
                onClick={() => setShowMore(false)}
                className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                <XIcon className="w-4 h-4" />
              </button>
            </div>

            {/* Grid of nav items */}
            <div className="grid grid-cols-3 gap-2 p-4 pb-8">
              {MORE_NAV.map(({ to, icon: Icon, label }) => {
                const isActive =
                  to === '/'
                    ? location.pathname === '/'
                    : location.pathname.startsWith(to);
                return (
                  <NavLink
                    key={to}
                    to={to}
                    end={to === '/'}
                    onClick={() => setShowMore(false)}
                    className={cn(
                      'flex flex-col items-center gap-2 p-3 rounded-xl border-2 transition-all',
                      isActive
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-950/50'
                        : 'border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50 hover:border-blue-300 hover:bg-blue-50 dark:hover:bg-blue-950/30'
                    )}
                  >
                    <Icon
                      className={cn('w-6 h-6', isActive ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400')}
                    />
                    <span className={cn(
                      'text-xs font-medium text-center leading-tight',
                      isActive ? 'text-blue-700 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300'
                    )}>
                      {label}
                    </span>
                  </NavLink>
                );
              })}
            </div>
          </div>
        </>
      )}

      {/* ── Main content ─────────────────────────────────────────── */}
      <main className="flex-1 md:ml-60 pt-14 md:pt-0 pb-16 md:pb-0">
        <div className="max-w-5xl mx-auto px-4 md:px-6 py-6">
          {children}
        </div>
      </main>
    </div>
  );
}
