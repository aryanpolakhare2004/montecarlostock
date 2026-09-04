# Vue 3 + TypeScript + Vite

mcstock's web dashboard frontend: Vue 3 (Composition API, `<script setup>`
SFCs), TypeScript, and Vite. Charts are rendered with Chart.js via
`vue-chartjs`. No router -- navigation is a single in-app tab state
(`src/navigation.ts`), with visited tabs kept mounted via a lazy-mount +
`v-show`-style pattern so form state and results survive switching tabs.

## Structure

- `src/pages/*.vue` -- one component per sidebar tab
- `src/components/*.vue` -- shared UI (buttons, tables, the asset
  simulate/backtest forms reused by Commodities/Crypto/Forex, etc.)
- `src/components/charts/*.vue` -- Chart.js wrappers (fan/band chart,
  histogram, categorical bar chart, fundamentals trend line chart)
- `src/composables/*.ts` -- shared reactive state (`useModels`, `useTheme`,
  `useToast`, `useThemeVersion` for re-theming charts on light/dark toggle)
- `src/api.ts`, `src/types.ts`, `src/format.ts`, `src/utils/*.ts` -- plain
  TypeScript, no framework dependency

## Scripts

- `npm run dev` -- Vite dev server (proxies `/api` to the FastAPI backend
  on `127.0.0.1:8000`)
- `npm run build` -- type-checks with `vue-tsc` then builds into
  `../mcstock/web/static/` (the path the FastAPI backend serves at `/`)
- `npm run lint` -- oxlint
