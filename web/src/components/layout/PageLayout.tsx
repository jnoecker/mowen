import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';
import s from './PageLayout.module.css';

export default function PageLayout() {
  return (
    <div className={s.layout}>
      <Navbar />
      <hr className="divider" />
      <main className={s.main}>
        <Outlet />
      </main>
    </div>
  );
}
