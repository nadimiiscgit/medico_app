import { NavLink, useLocation } from 'react-router-dom';
import { cn } from '../lib/utils';
import {
  HomeIcon,
  ListIcon,
  ClockIcon,
  BookOpenIcon,
  BookmarkIcon,
  BarChart3Icon,
  SettingsIcon,
  BrainIcon,
} from 'lucide-react';

const NAV_ITEMS = [
  { to: '/', icon: HomeIcon, label: 'Home' },
  { to: '/browse', icon: ListIcon, label: 'Browse' },
  { to: '/practice', icon: ClockIcon, label: 'Practice Test' },
  { to: '/quiz', icon: BookOpenIcon, label: 'Quiz Mode' },
  { to: '/bookmarks', icon: BookmarkIcon, label: 'Bookmarks' },
  { to: '/analytics', icon: BarChart3Icon, label: 'Analytics' },
  { to: '/settings', icon: SettingsIcon, label: 'Settings' },
];

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const location = useLocation();

  return (
    <div className="flex min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Sidebar */}
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
        <nav className="flex-1 px-3 py-4 space-y-1">
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
                  <Icon className={cn('flex-shrink-0', isActive ? 'text-blue-600 dark:text-blue-400' : 'text-gray-400 dark:text-gray-500')} style={{width: '18px', height: '18px'}} />
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

      {/* Mobile top bar */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-20 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-blue-600 rounded-lg flex items-center justify-center">
            <BrainIcon className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-gray-900 dark:text-gray-100 text-sm">NEET PG QB</span>
        </div>
      </div>

      {/* Mobile bottom nav */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-20 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 flex">
        {NAV_ITEMS.slice(0, 5).map(({ to, icon: Icon, label }) => (
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
      </nav>

      {/* Main content */}
      <main className="flex-1 md:ml-60 pt-14 md:pt-0 pb-16 md:pb-0">
        <div className="max-w-5xl mx-auto px-4 md:px-6 py-6">
          {children}
        </div>
      </main>
    </div>
  );
}
