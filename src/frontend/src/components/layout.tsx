import { NavLink, Outlet } from 'react-router-dom';

const navigation = [
  { path: '/dashboard', label: 'Dashboard' },
  { path: '/profile', label: 'My Profile' },
  { path: '/cv', label: 'My CV' },
  { path: '/skills-assessment', label: 'Skills Assessment' },
  { path: '/roadmap', label: 'Learning Roadmap' },
  { path: '/mentor', label: 'AI Mentor' },
];

export default function WorkspaceLayout() {
  return (
    <div className="cf-workspace-layout">
      <aside className="cf-workspace-sidebar">
        <span className="cf-sidebar-label">WORKSPACE</span>

        <nav
          className="cf-workspace-nav"
          aria-label="Workspace navigation"
        >
          {navigation.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end
              className={({ isActive }) =>
                `cf-nav-link ${
                  isActive ? 'cf-nav-active' : ''
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <main className="cf-workspace-content" id="main-content">
        <Outlet />
      </main>
    </div>
  );
}