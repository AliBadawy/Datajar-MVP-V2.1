import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Loader2 } from "lucide-react"
import { useAppStore } from "../lib/store"

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()
  
  // Use Zustand store for authentication
  const login = useAppStore(state => state.login)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setIsLoading(true)

    try {
      // Use the login function from our store instead of direct Supabase call
      await login(email, password)
      navigate("/projects") // Redirect after login
    } catch (err: any) {
      console.error("Login error:", err)
      setError(err.message || "Failed to login")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-10 p-6 bg-white rounded shadow">
      <h2 className="text-xl font-bold mb-4">Log In to DataJar</h2>
      <form onSubmit={handleLogin} className="space-y-4">
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="w-full border p-2 rounded"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="w-full border p-2 rounded"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-black text-white py-2 rounded hover:bg-gray-800 transition flex items-center justify-center"
        >
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Logging in...
            </>
          ) : (
            "Log In"
          )}
        </button>
        {error && <p className="text-red-600">{error}</p>}
        <p className="text-sm text-center mt-4">
          Don't have an account?{" "}
          <a 
            href="/signup"
            onClick={(e) => {
              e.preventDefault()
              navigate("/signup")
            }}
            className="text-blue-600 hover:underline"
          >
            Sign up
          </a>
        </p>
      </form>
    </div>
  )
}