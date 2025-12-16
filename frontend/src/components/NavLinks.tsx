import { Link, useLocation } from 'react-router-dom'
import styles from './NavLinks.module.css'

interface NavLinksProps {
  variant?: 'dark' | 'light' | 'gradient'
}

const NavLinks = ({ variant = 'dark' }: NavLinksProps) => {
  const location = useLocation()

  const links = [
    { path: '/level-test', label: '레벨 테스트' },
    { path: '/recommend', label: '추천' },
    { path: '/', label: 'HOME' },
    { path: '/dropout', label: '이탈 분석' },
    { path: '/courses', label: '강의 분석' }
    
  ]

  return (
    <nav className={`${styles.navLinks} ${styles[variant]}`}>
      {links.map((link) => (
        <Link
          key={link.path}
          to={link.path}
          className={`${styles.link} ${location.pathname === link.path ? styles.active : ''}`}
        >
          {link.label}
        </Link>
      ))}
    </nav>
  )
}

export default NavLinks
