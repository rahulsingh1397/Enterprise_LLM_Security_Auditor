import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

const TOKEN_KEY = 'llm_audit_token'
const USER_KEY = 'llm_audit_user'

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY))
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem(USER_KEY)) } catch { return null }
  })

  const login = (tokenData) => {
    const { access_token, user_id, name, role } = tokenData
    localStorage.setItem(TOKEN_KEY, access_token)
    const u = { id: user_id, name, role }
    localStorage.setItem(USER_KEY, JSON.stringify(u))
    setToken(access_token)
    setUser(u)
  }

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ token, user, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY)
}
