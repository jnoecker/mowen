import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';
import s from './PageLayout.module.css';

export default function PageLayout() {
  return (
    <div className={s.layout}>
      <a href="#main-content" className="skip-to-content">
        Skip to content
      </a>
      <Navbar />
      <hr className="divider" />
      <main id="main-content" className={s.main}>
        <Outlet />
      </main>
      <footer className={s.footer}>
        &copy; 2026 John Noecker Jr.
      </footer>
    </div>
  );
}
