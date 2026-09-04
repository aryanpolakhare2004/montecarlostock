<script setup lang="ts">
import { ref } from 'vue';
import { useModels } from './composables/useModels';
import ToastProvider from './components/ToastProvider.vue';
import ThemeToggle from './components/ThemeToggle.vue';
import DashboardPage from './pages/DashboardPage.vue';
import PricePage from './pages/PricePage.vue';
import StrategyPage from './pages/StrategyPage.vue';
import ComparePage from './pages/ComparePage.vue';
import PortfolioPage from './pages/PortfolioPage.vue';
import EquitiesPage from './pages/EquitiesPage.vue';
import TrainPage from './pages/TrainPage.vue';
import PredictPage from './pages/PredictPage.vue';
import BacktestMlPage from './pages/BacktestMlPage.vue';
import AnalystPage from './pages/AnalystPage.vue';
import AnalystComparePage from './pages/AnalystComparePage.vue';
import SentimentPage from './pages/SentimentPage.vue';
import CommoditiesPage from './pages/CommoditiesPage.vue';
import CryptoPage from './pages/CryptoPage.vue';
import ForexPage from './pages/ForexPage.vue';
import WatchlistPage from './pages/WatchlistPage.vue';
import TerminalPage from './pages/TerminalPage.vue';
import HistoryPage from './pages/HistoryPage.vue';
import { NAV_GROUPS, type TabId } from './navigation';

const tab = ref<TabId>('dashboard');
const visited = ref<Set<TabId>>(new Set(['dashboard']));
const sidebarOpen = ref(false);
const modelOptions = useModels();

function navigate(next: TabId) {
  tab.value = next;
  if (!visited.value.has(next)) {
    visited.value = new Set(visited.value).add(next);
  }
  sidebarOpen.value = false;
}

function isVisited(id: TabId): boolean {
  return visited.value.has(id);
}
</script>

<template>
  <ToastProvider>
    <div class="app-shell">
      <button
        type="button" class="sidebar-toggle" aria-label="Toggle navigation"
        @click="sidebarOpen = !sidebarOpen"
      >
        ☰
      </button>

      <aside :class="`sidebar${sidebarOpen ? ' open' : ''}`">
        <div class="sidebar-header">
          <div>
            <h1>mcstock</h1>
            <p class="subtitle">Monte Carlo &middot; ML &middot; AI analyst</p>
          </div>
          <ThemeToggle />
        </div>
        <nav>
          <div class="nav-group" v-for="group in NAV_GROUPS" :key="group.label">
            <div class="nav-group-label">{{ group.label }}</div>
            <button
              v-for="item in group.items" :key="item.id"
              :class="`nav-btn${tab === item.id ? ' active' : ''}`"
              @click="navigate(item.id)"
            >
              <component :is="item.icon" />
              <span>{{ item.label }}</span>
            </button>
          </div>
        </nav>
      </aside>

      <main>
        <div v-if="isVisited('dashboard')" :class="tab === 'dashboard' ? '' : 'tab-hidden'">
          <DashboardPage @navigate="navigate" />
        </div>
        <div v-if="isVisited('price')" :class="tab === 'price' ? '' : 'tab-hidden'">
          <PricePage />
        </div>
        <div v-if="isVisited('strategy')" :class="tab === 'strategy' ? '' : 'tab-hidden'">
          <StrategyPage :model-options="modelOptions" />
        </div>
        <div v-if="isVisited('compare')" :class="tab === 'compare' ? '' : 'tab-hidden'">
          <ComparePage :model-options="modelOptions" />
        </div>
        <div v-if="isVisited('portfolio')" :class="tab === 'portfolio' ? '' : 'tab-hidden'">
          <PortfolioPage />
        </div>
        <div v-if="isVisited('equities')" :class="tab === 'equities' ? '' : 'tab-hidden'">
          <EquitiesPage />
        </div>
        <div v-if="isVisited('commodities')" :class="tab === 'commodities' ? '' : 'tab-hidden'">
          <CommoditiesPage />
        </div>
        <div v-if="isVisited('crypto')" :class="tab === 'crypto' ? '' : 'tab-hidden'">
          <CryptoPage />
        </div>
        <div v-if="isVisited('forex')" :class="tab === 'forex' ? '' : 'tab-hidden'">
          <ForexPage />
        </div>
        <div v-if="isVisited('train')" :class="tab === 'train' ? '' : 'tab-hidden'">
          <TrainPage @trained="modelOptions.reload" />
        </div>
        <div v-if="isVisited('predict')" :class="tab === 'predict' ? '' : 'tab-hidden'">
          <PredictPage :model-options="modelOptions" />
        </div>
        <div v-if="isVisited('backtest_ml')" :class="tab === 'backtest_ml' ? '' : 'tab-hidden'">
          <BacktestMlPage :model-options="modelOptions" />
        </div>
        <div v-if="isVisited('analyst')" :class="tab === 'analyst' ? '' : 'tab-hidden'">
          <AnalystPage />
        </div>
        <div v-if="isVisited('analyst_compare')" :class="tab === 'analyst_compare' ? '' : 'tab-hidden'">
          <AnalystComparePage />
        </div>
        <div v-if="isVisited('sentiment')" :class="tab === 'sentiment' ? '' : 'tab-hidden'">
          <SentimentPage />
        </div>
        <div v-if="isVisited('watchlist')" :class="tab === 'watchlist' ? '' : 'tab-hidden'">
          <WatchlistPage />
        </div>
        <div v-if="isVisited('terminal')" :class="tab === 'terminal' ? '' : 'tab-hidden'">
          <TerminalPage />
        </div>
        <div v-if="isVisited('history')" :class="tab === 'history' ? '' : 'tab-hidden'">
          <HistoryPage />
        </div>
      </main>
    </div>
  </ToastProvider>
</template>
