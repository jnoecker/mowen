import { NavLink } from 'react-router-dom';
import logoUrl from '../../assets/logo.png';
import sealUrl from '../../assets/seal.svg';
import s from './Navbar.module.css';

const navItems = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/documents', label: 'Documents' },
  { to: '/corpora', label: 'Corpora' },
  { to: '/experiments', label: 'Experiments' },
];

export default function Navbar() {
  return (
    <nav className={s.nav}>
      <NavLink to="/dashboard" className={s.brand}>
        <span className={s.logoWrap}>
          <img src={logoUrl} alt="" className={s.logo} />
          <img src={sealUrl} alt="墨" className={s.seal} />
        </span>
        mowen <span className={s.brandCjk}>(墨紋)</span>
      </NavLink>
      <ul className={s.links}>
        {navItems.map(({ to, label }) => (
          <li key={to}>
            <NavLink
              to={to}
              className={({ isActive }) =>
                `${s.link}${isActive ? ` ${s.linkActive}` : ''}`
              }
            >
              {label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
