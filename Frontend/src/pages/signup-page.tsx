import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAppStore } from "../lib/store"

export default function SignupPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [localError, setLocalError] = useState("")
  const navigate = useNavigate()
  
  // Get auth state and actions from the store
  const signup = useAppStore(state => state.signup)
  const authLoading = useAppStore(state => state.authLoading)
  const authError = useAppStore(state => state.authError)

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError("")

    try {
      // Use the store's signup method instead of calling Supabase directly
      await signup(email, password)
      // If we get here, signup was successful
      navigate("/projects")
    } catch (error) {
      if (error instanceof Error) {
        setLocalError(error.message)
      } else {
        setLocalError("An unknown error occurred during signup")
      }
    }
  }

  return (
    <div className="max-w-md mx-auto mt-20 p-6 border rounded shadow bg-white">
      <h1 className="text-xl font-semibold mb-4">Sign Up</h1>
      <form onSubmit={handleSignup} className="space-y-4">
        <input
          className="w-full p-2 border rounded"
          placeholder="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          className="w-full p-2 border rounded"
          placeholder="Password (min 6 chars)"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={6}
        />
        {(localError || authError) && (
          <p className="text-red-500 text-sm">{localError || authError}</p>
        )}
        <button 
          className="w-full bg-black text-white p-2 rounded hover:bg-gray-800 disabled:bg-gray-400 disabled:cursor-not-allowed" 
          disabled={authLoading}
        >
          {authLoading ? "Creating Account..." : "Create Account"}
        </button>
        
        <p className="text-sm text-center mt-4">
          Already have an account?{" "}
          <a 
            href="/login"
            onClick={(e) => {
              e.preventDefault()
              navigate("/login")
            }}
            className="text-blue-600 hover:underline"
          >
            Log in
          </a>
        </p>
      </form>
    </div>
  )
}
