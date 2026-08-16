import { ClerkProvider } from '@clerk/react'
import { createRoot } from 'react-dom/client'
import { App } from './App'
import { AuthGate } from './components/AuthGate'
import { CLERK_PUBLISHABLE_KEY, clerkAppearance, clerkEnabled } from './lib/clerk'
import './index.css'

const root = createRoot(document.getElementById('root')!)

if (clerkEnabled) {
  root.render(
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY} afterSignOutUrl="/" appearance={clerkAppearance}>
      <AuthGate>
        <App />
      </AuthGate>
    </ClerkProvider>,
  )
} else {
  root.render(<App />)
}
