import { Link } from 'react-router-dom'

function NotFoundPage() {
  return (
    <div style={{ padding: '2rem', textAlign: 'center' }}>
      <h1>404 - Page Not Found</h1>
      <p>The page you're looking for doesn't exist.</p>
      <Link to="/" style={{ marginTop: '1rem', display: 'inline-block', color: '#007bff' }}>
        Go back home
      </Link>
    </div>
  )
}

export default NotFoundPage
