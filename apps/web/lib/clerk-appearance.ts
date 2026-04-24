/** Clerk `<SignIn />` / `<SignUp />` styling — aligned with Candidate Hub + teal primary (#00685f). */
export const clerkAppearance = {
  variables: {
    colorPrimary: '#00685f',
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
      'bg-[#00685f] text-white hover:bg-[#005a52] shadow-sm border border-[0.5px] border-teal-800/30',
    footerActionLink: 'text-teal-700 hover:text-teal-800 font-medium dark:text-teal-400 dark:hover:text-teal-300',
    formFieldInput:
      'border-[0.5px] border-slate-200 bg-slate-50/80 text-[#171d1c] focus:border-teal-500 focus:ring-teal-500/20 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100',
    identityPreviewText: 'text-[#171d1c] dark:text-slate-100',
    formFieldLabel: 'text-[#3d4947] dark:text-slate-400',
    dividerLine: 'bg-slate-200 dark:bg-slate-700',
    dividerText: 'text-slate-500 dark:text-slate-400',
    footer: 'text-[#3d4947] dark:text-slate-400',
  },
}
