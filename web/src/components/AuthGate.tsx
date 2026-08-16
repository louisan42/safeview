import { Show, SignIn, useAuth } from '@clerk/react'
import type { ReactNode } from 'react'
import { clerkAppearance } from '../lib/clerk'

type AuthGateProps = {
  children: ReactNode
}

export function AuthGate({ children }: AuthGateProps) {
  const { isLoaded } = useAuth()

  if (!isLoaded) {
    return (
      <div className="grid h-full place-items-center bg-sv-paper px-4">
        <p className="font-display text-lg font-bold tracking-tight text-sv-ink">Loading Watchtile…</p>
      </div>
    )
  }

  return (
    <>
      <Show when="signed-out">
        <div className="grid h-full place-items-center bg-sv-paper px-4">
          <div className="sv-panel w-full max-w-md rounded-md px-6 py-6 text-center">
            <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-sv-accent">Neighbourhood</div>
            <h1 className="font-display text-2xl font-bold tracking-tight text-sv-ink">Watchtile</h1>
            <p className="mt-2 text-sm text-sv-muted">Sign in with the staging Clerk development instance to preview this map.</p>
            <div className="mt-4 flex justify-center">
              <SignIn routing="hash" appearance={clerkAppearance} />
            </div>
          </div>
        </div>
      </Show>
      <Show when="signed-in">{children}</Show>
    </>
  )
}
