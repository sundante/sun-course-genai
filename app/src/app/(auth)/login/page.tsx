export default function LoginPage() {
  return (
    <main className="min-h-screen bg-sun-bg flex items-center justify-center px-4">
      <div className="w-full max-w-sm bg-white rounded-2xl border border-sun-yellow-bdr p-8 shadow-sm">
        <h1 className="text-xl font-bold text-sun-dark mb-1">Sign in</h1>
        <p className="text-sm text-sun-muted mb-6">
          Enter your email to receive a magic link.
        </p>
        <form className="space-y-4">
          <input
            type="email"
            placeholder="you@example.com"
            className="w-full h-9 px-3 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-sun-yellow"
          />
          <button
            type="submit"
            className="w-full h-9 rounded-lg bg-sun-yellow text-sun-dark text-sm font-semibold hover:bg-sun-yellow-dk transition-colors"
          >
            Send magic link
          </button>
        </form>
        <p className="text-xs text-sun-muted text-center mt-4">
          Authentication coming in Phase 2.
        </p>
      </div>
    </main>
  );
}
