import { FormEvent, useState } from 'react'
import { CheckCircle2, Copy, FlaskConical, ShieldCheck } from 'lucide-react'
import type { Session } from '@supabase/supabase-js'
import { supabase } from './lib/supabase'

export function LoginScreen() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setMessage(null)
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { shouldCreateUser: true, emailRedirectTo: window.location.origin },
    })
    setBusy(false)
    if (error) setMessage(error.message)
    else setSent(true)
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo"><FlaskConical size={26} /></div>
        <div className="eyebrow">HRP TRANSFER LAB</div>
        <h1>Evidence Workbench</h1>
        <p className="auth-intro">Review intervention evidence, route classifications, transfer outcomes and product relevance in the live HRP Transfer Evidence Registry.</p>
        {sent ? (
          <div className="success-box"><CheckCircle2 size={20} /><div><strong>Check your email</strong><p>Use the secure Supabase sign-in link, then return here.</p></div></div>
        ) : (
          <form onSubmit={submit}>
            <label className="field-label" htmlFor="email">Reviewer email</label>
            <input id="email" className="text-input" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
            <button className="primary-button full" disabled={busy}>{busy ? 'Sending…' : 'Send secure sign-in link'}</button>
          </form>
        )}
        {message && <div className="form-error">{message}</div>}
        <div className="auth-footnote"><ShieldCheck size={15} /> Authentication alone does not grant evidence access. An active Workbench role is also required by database RLS.</div>
      </div>
    </div>
  )
}

export function PendingAccess({ session, onRetry }: { session: Session; onRetry: () => void }) {
  const [copied, setCopied] = useState(false)
  async function copy() {
    await navigator.clipboard.writeText(session.user.id)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }
  return (
    <div className="auth-page">
      <div className="auth-card pending-card">
        <div className="auth-logo amber"><ShieldCheck size={25} /></div>
        <div className="eyebrow">SIGNED IN · ROLE REQUIRED</div>
        <h1>Workbench access pending</h1>
        <p className="auth-intro">Your Supabase identity is valid, but it has not yet been assigned a Workbench role. Send the user ID below to the database owner to be added as viewer, editor or owner.</p>
        <div className="uid-box"><code>{session.user.id}</code><button onClick={copy}>{copied ? <CheckCircle2 size={17} /> : <Copy size={17} />}</button></div>
        <button className="primary-button full" onClick={onRetry}>Check access again</button>
        <button className="secondary-button full" onClick={() => supabase.auth.signOut()}>Sign out</button>
      </div>
    </div>
  )
}
