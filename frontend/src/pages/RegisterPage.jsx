import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import useAuthStore from '../store/authStore'

function RegisterPage() {
  const navigate = useNavigate()
  const { register, isLoading, error, clearError } = useAuthStore()
  
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    first_name: '',
    last_name: '',
    phone_number: '',
    password: '',
    password_confirm: '',
  })
  
  const [formErrors, setFormErrors] = useState({})

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
    clearError()
    setFormErrors({})
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // Client-side validation
    if (formData.password !== formData.password_confirm) {
      setFormErrors({ password: "Passwords don't match" })
      return
    }
    
    const result = await register(formData)
    
    if (result.success) {
      navigate('/')
    } else {
      setFormErrors(result.error)
    }
  }

  return (
    <div style={{ 
      maxWidth: '500px', 
      margin: '50px auto', 
      padding: '2rem',
      border: '1px solid #ddd',
      borderRadius: '8px'
    }}>
      <h1 style={{ textAlign: 'center', marginBottom: '2rem' }}>Register</h1>
      
      {error && (
        <div style={{ 
          padding: '1rem', 
          marginBottom: '1rem', 
          backgroundColor: '#fee', 
          color: '#c00',
          borderRadius: '4px'
        }}>
          {typeof error === 'string' ? error : 'Registration failed. Please check your inputs.'}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem' }}>
              First Name *
            </label>
            <input
              type="text"
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              required
              style={{ 
                width: '100%', 
                padding: '0.5rem',
                fontSize: '1rem',
                border: '1px solid #ddd',
                borderRadius: '4px'
              }}
            />
            {formErrors.first_name && <span style={{ color: '#c00', fontSize: '0.875rem' }}>{formErrors.first_name}</span>}
          </div>
          
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem' }}>
              Last Name *
            </label>
            <input
              type="text"
              name="last_name"
              value={formData.last_name}
              onChange={handleChange}
              required
              style={{ 
                width: '100%', 
                padding: '0.5rem',
                fontSize: '1rem',
                border: '1px solid #ddd',
                borderRadius: '4px'
              }}
            />
            {formErrors.last_name && <span style={{ color: '#c00', fontSize: '0.875rem' }}>{formErrors.last_name}</span>}
          </div>
        </div>
        
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem' }}>
            Email *
          </label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
            style={{ 
              width: '100%', 
              padding: '0.5rem',
              fontSize: '1rem',
              border: '1px solid #ddd',
              borderRadius: '4px'
            }}
          />
          {formErrors.email && <span style={{ color: '#c00', fontSize: '0.875rem' }}>{formErrors.email}</span>}
        </div>
        
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem' }}>
            Username *
          </label>
          <input
            type="text"
            name="username"
            value={formData.username}
            onChange={handleChange}
            required
            style={{ 
              width: '100%', 
              padding: '0.5rem',
              fontSize: '1rem',
              border: '1px solid #ddd',
              borderRadius: '4px'
            }}
          />
          {formErrors.username && <span style={{ color: '#c00', fontSize: '0.875rem' }}>{formErrors.username}</span>}
        </div>
        
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem' }}>
            Phone Number (e.g., 0712345678)
          </label>
          <input
            type="tel"
            name="phone_number"
            value={formData.phone_number}
            onChange={handleChange}
            placeholder="0712345678"
            style={{ 
              width: '100%', 
              padding: '0.5rem',
              fontSize: '1rem',
              border: '1px solid #ddd',
              borderRadius: '4px'
            }}
          />
          {formErrors.phone_number && <span style={{ color: '#c00', fontSize: '0.875rem' }}>{formErrors.phone_number}</span>}
        </div>
        
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem' }}>
            Password *
          </label>
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            required
            style={{ 
              width: '100%', 
              padding: '0.5rem',
              fontSize: '1rem',
              border: '1px solid #ddd',
              borderRadius: '4px'
            }}
          />
          {formErrors.password && <span style={{ color: '#c00', fontSize: '0.875rem' }}>{formErrors.password}</span>}
        </div>
        
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem' }}>
            Confirm Password *
          </label>
          <input
            type="password"
            name="password_confirm"
            value={formData.password_confirm}
            onChange={handleChange}
            required
            style={{ 
              width: '100%', 
              padding: '0.5rem',
              fontSize: '1rem',
              border: '1px solid #ddd',
              borderRadius: '4px'
            }}
          />
        </div>
        
        <button
          type="submit"
          disabled={isLoading}
          style={{ 
            width: '100%', 
            padding: '0.75rem',
            fontSize: '1rem',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: isLoading ? 'not-allowed' : 'pointer'
          }}
        >
          {isLoading ? 'Registering...' : 'Register'}
        </button>
      </form>
      
      <p style={{ textAlign: 'center', marginTop: '1.5rem' }}>
        Already have an account? <Link to="/login" style={{ color: '#007bff' }}>Login</Link>
      </p>
    </div>
  )
}

export default RegisterPage
