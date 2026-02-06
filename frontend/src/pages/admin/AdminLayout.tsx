/**
 * Admin Layout - Shared layout for all admin pages
 */
import { Outlet, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, GitBranch, Settings, ArrowLeft } from 'lucide-react';

const adminNavItems = [
  { path: '/admin/discussion-pipeline', label: 'Pipeline', icon: GitBranch },
  { path: '/admin/settings', label: 'Settings', icon: Settings },
];

export function AdminLayout() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Admin Header */}
      <header className="bg-gray-900 text-white">
        <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/" className="flex items-center gap-2 text-gray-400 hover:text-white">
              <ArrowLeft size={16} />
              <span className="text-sm">Back to App</span>
            </Link>
            <div className="w-px h-5 bg-gray-700" />
            <div className="flex items-center gap-2">
              <LayoutDashboard size={20} />
              <span className="font-medium">CoRead Admin</span>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="max-w-6xl mx-auto px-6">
          <div className="flex gap-1">
            {adminNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-2 px-4 py-2 text-sm rounded-t-lg transition-colors ${
                    isActive
                      ? 'bg-gray-50 text-gray-900'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'
                  }`}
                >
                  <Icon size={16} />
                  {item.label}
                </Link>
              );
            })}
          </div>
        </nav>
      </header>

      {/* Content */}
      <main>
        <Outlet />
      </main>
    </div>
  );
}
