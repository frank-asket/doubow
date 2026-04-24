import coreWebVitals from 'eslint-config-next/core-web-vitals'

/** @type {import('eslint').Linter.Config[]} */
const eslintConfig = [
  ...coreWebVitals,
  {
    rules: {
      'react/react-in-jsx-scope': 'off',
      // Stricter than historical `next lint` runs; revisit as refactors land.
      'react-hooks/set-state-in-effect': 'off',
      'react/no-unescaped-entities': 'off',
    },
  },
]

export default eslintConfig
