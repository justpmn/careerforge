import { Outlet } from 'react-router-dom';
import Brand from './Brand';
import ThemeToggle from './ThemeToggle';

type Props = { theme: 'light' | 'dark'; toggleTheme: () => void };

export default function AuthLayout({ theme, toggleTheme }: Props) {
  return (
    <div className="auth-shell">
      <aside className="auth-intro">
        <Brand />
        <div className="intro-center">
          <div className="eyebrow"><span className="eyebrow-dot" /> CAREER DEVELOPMENT, REBUILT</div>
          <h1>Your next step<br />starts <em>here.</em></h1>
          <p>Find your strengths. Spot the gaps. Build a learning path that actually moves you forward.</p>
          <div className="path-steps" aria-label="Your career journey">
            <div className="path-step"><span className="path-index done">01</span><span>Know your skills</span><span className="path-end">✓</span></div>
            <div className="path-step"><span className="path-index current">02</span><span>Find your direction</span><span className="path-end">↗</span></div>
            <div className="path-step"><span className="path-index">03</span><span>Keep progressing</span><span className="path-end">—</span></div>
          </div>
        </div>
        <span className="intro-bottom">BUILT FOR THE WAY DEVELOPERS GROW.</span>
      </aside>
      <main className="auth-main">
        <div className="mobile-brand"><Brand /></div>
        <div className="auth-top"><ThemeToggle theme={theme} toggle={toggleTheme} /></div>
        <div className="auth-main-content"><Outlet /></div>
        <p className="auth-footer">© {new Date().getFullYear()} CareerForge. Built for progress.</p>
      </main>
    </div>
  );
}
