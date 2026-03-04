import { Link } from 'react-router-dom'
import useAuthStore from '../store/authStore'

function HomePage() {
  const { user, isAuthenticated, logout } = useAuthStore()

  return (
    <div style={{ padding: '2rem', textAlign: 'center' }}>
      <h1>SmartCommerce Kenya</h1>
      <p>Welcome to SmartCommerce Kenya - Your trusted e-commerce platform</p>
      
      {isAuthenticated ? (
        <div style={{ marginTop: '2rem' }}>
          <p>Welcome back, {user?.full_name || user?.email}!</p>
          {!user?.is_email_verified && (
            <p style={{ color: '#f90', marginTop: '0.5rem' }}>
              Please verify your email address
            </p>
          )}
          <button
            onClick={logout}
            style={{
              marginTop: '1rem',
              padding: '0.5rem 1rem',
              backgroundColor: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Logout
          </button>
        </div>
      ) : (
        <div style={{ marginTop: '2rem' }}>
          <Link
            to="/login"
            style={{
              display: 'inline-block',
              marginRight: '1rem',
              padding: '0.5rem 1rem',
              backgroundColor: '#007bff',
              color: 'white',
              textDecoration: 'none',
              borderRadius: '4px'
            }}
          >
            Login
          </Link>
          <Link
            to="/register"
            style={{
              display: 'inline-block',
              padding: '0.5rem 1rem',
              backgroundColor: '#28a745',
              color: 'white',
              textDecoration: 'none',
              borderRadius: '4px'
            }}
          >
            Register
          </Link>
        </div>
      )}
      
      <p style={{ marginTop: '2rem', color: '#666' }}>
        Phase 3 complete: JWT Authentication with registration, login, and email verification
      </p>
    </div>
  )
}

export default HomePage
