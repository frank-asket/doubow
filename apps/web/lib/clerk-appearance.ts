/** Clerk `<SignIn />` / `<SignUp />` styling — aligned with app brand (primary green #14603b). */
export const clerkAppearance = {
  variables: {
    colorPrimary: '#14603b',
    colorBackground: '#ffffff',
    colorInputBackground: '#f8fafc',
    colorInputText: '#171d1c',
    colorText: '#171d1c',
    colorTextSecondary: '#3d4947',
    colorNeutral: '#64748b',
    borderRadius: '0.5rem',
    fontFamily: 'var(--font-sans), ui-sans-serif, system-ui, sans-serif',
  },
  elements: {
    rootBox: 'w-full',
    card: 'w-full rounded-xl border border-[0.5px] border-slate-200 bg-white shadow-lg shadow-slate-900/5 dark:border-slate-700 dark:bg-slate-900',
    headerTitle: 'text-[#171d1c] dark:text-slate-100 font-semibold tracking-tight',
    headerSubtitle: 'text-[#3d4947] dark:text-slate-400',
    socialButtonsBlockButton:
      'border-[0.5px] border-slate-200 bg-white text-[#171d1c] hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700',
    formButtonPrimary:
      'bg-[#14603b] text-white hover:bg-[#0f4d30] shadow-sm border border-[0.5px] border-[#14603b]/35',
    footerActionLink:
      'text-[#14603b] hover:text-[#0f4d30] font-medium dark:text-emerald-400 dark:hover:text-emerald-300',
    formFieldInput:
      'border-[0.5px] border-slate-200 bg-slate-50/80 text-[#171d1c] focus:border-[#2ea44f] focus:ring-[#2ea44f]/20 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100',
    identityPreviewText: 'text-[#171d1c] dark:text-slate-100',
    formFieldLabel: 'text-[#3d4947] dark:text-slate-400',
    dividerLine: 'bg-slate-200 dark:bg-slate-700',
    dividerText: 'text-slate-500 dark:text-slate-400',
    footer: 'text-[#3d4947] dark:text-slate-400',
  },
}
