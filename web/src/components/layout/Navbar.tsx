import { NavLink } from 'react-router-dom';

const navItems = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/documents', label: 'Documents' },
  { to: '/corpora', label: 'Corpora' },
  { to: '/experiments/new', label: 'Experiments' },
];

export default function Navbar() {
  return (
    <nav style={styles.nav}>
      <NavLink to="/dashboard" style={styles.brand}>
        mowen <span style={styles.brandCjk}>(&#x58A8;&#x7D0B;)</span>
      </NavLink>
      <ul style={styles.links}>
        {navItems.map(({ to, label }) => (
          <li key={to}>
            <NavLink
              to={to}
              style={({ isActive }) => ({
                ...styles.link,
                ...(isActive ? styles.activeLink : {}),
              })}
            >
              {label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}

const styles: Record<string, React.CSSProperties> = {
  nav: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 1.5rem',
    height: '3.5rem',
    backgroundColor: '#1a1a2e',
    borderBottom: '1px solid #2a2a4a',
  },
  brand: {
    color: '#e0e0e0',
    textDecoration: 'none',
    fontSize: '1.25rem',
    fontWeight: 700,
    letterSpacing: '0.02em',
  },
  brandCjk: {
    fontSize: '0.85rem',
    opacity: 0.7,
    fontWeight: 400,
  },
  links: {
    display: 'flex',
    listStyle: 'none',
    margin: 0,
    padding: 0,
    gap: '0.25rem',
  },
  link: {
    color: '#a0a0c0',
    textDecoration: 'none',
    padding: '0.5rem 0.75rem',
    borderRadius: '6px',
    fontSize: '0.9rem',
    transition: 'color 0.15s, background-color 0.15s',
  },
  activeLink: {
    color: '#e0e0e0',
    backgroundColor: '#2a2a4a',
  },
};
