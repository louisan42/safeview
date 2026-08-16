import { UserButton } from '@clerk/react'
import { clerkAppearance } from '../lib/clerk'

export function AuthBar() {
  return <UserButton appearance={clerkAppearance} />
}
