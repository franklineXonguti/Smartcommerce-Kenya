import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '../services/api'

const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Login action
      login: async (email, password) => {
        set({ isLoading: true, error: null })
        try {
          const response = await api.post('/auth/login/', { email, password })
          const { access, refresh } = response.data
          
          // Store tokens
          localStorage.setItem('access_token', access)
          localStorage.setItem('refresh_token', refresh)
          
          // Fetch user profile
          const profileResponse = await api.get('/users/profile/')
          
          set({
            user: profileResponse.data,
            accessToken: access,
            refreshToken: refresh,
            isAuthenticated: true,
            isLoading: false,
          })
          
          return { success: true }
        } catch (error) {
          const errorMessage = error.response?.data?.detail || 'Login failed'
          set({ error: errorMessage, isLoading: false })
          return { success: false, error: errorMessage }
        }
      },

      // Register action
      register: async (userData) => {
        set({ isLoading: true, error: null })
        try {
          const response = await api.post('/auth/register/', userData)
          const { user, tokens } = response.data
          
          // Store tokens
          localStorage.setItem('access_token', tokens.access)
          localStorage.setItem('refresh_token', tokens.refresh)
          
          set({
            user,
            accessToken: tokens.access,
            refreshToken: tokens.refresh,
            isAuthenticated: true,
            isLoading: false,
          })
          
          return { success: true, message: response.data.message }
        } catch (error) {
          const errorMessage = error.response?.data || 'Registration failed'
          set({ error: errorMessage, isLoading: false })
          return { success: false, error: errorMessage }
        }
      },

      // Logout action
      logout: () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          error: null,
        })
      },

      // Fetch user profile
      fetchProfile: async () => {
        try {
          const response = await api.get('/users/profile/')
          set({ user: response.data })
          return { success: true }
        } catch (error) {
          return { success: false, error: error.response?.data }
        }
      },

      // Update user profile
      updateProfile: async (userData) => {
        set({ isLoading: true, error: null })
        try {
          const response = await api.patch('/users/profile/', userData)
          set({ user: response.data, isLoading: false })
          return { success: true }
        } catch (error) {
          const errorMessage = error.response?.data || 'Update failed'
          set({ error: errorMessage, isLoading: false })
          return { success: false, error: errorMessage }
        }
      },

      // Clear error
      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

export default useAuthStore
