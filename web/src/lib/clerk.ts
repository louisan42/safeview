export const CLERK_PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY ?? ''

export const clerkEnabled = Boolean(CLERK_PUBLISHABLE_KEY)

export const clerkAppearance = {
  variables: {
    colorPrimary: '#2563EB',
    colorBackground: '#f7f4ee',
    colorNeutral: '#292524',
    colorText: '#292524',
    colorTextSecondary: '#78716c',
    borderRadius: '0.375rem',
    fontFamily: 'Nunito, sans-serif',
  },
} as const
