<script setup lang="ts">
import { ref } from 'vue';
import { api } from '../api';
import Sparkline from '../components/Sparkline.vue';
import { fmtMoney, fmtPct, fmtScore } from '../format';
import type { ModelRecord, RunRecord, WatchlistEntry } from '../types';
import type { TabId } from '../navigation';

const emit = defineEmits<{ navigate: [tab: TabId] }>();

const watchlist = ref<WatchlistEntry[] | null>(null);
const runs = ref<RunRecord[] | null>(null);
const models = ref<ModelRecord[] | null>(null);

api.listWatchlist().then((r) => { watchlist.value = r.tickers; }).catch(() => { watchlist.value = []; });
api.listRuns(500).then((r) => { runs.value = r; }).catch(() => { runs.value = []; });
api.listModels().then((r) => { models.value = r; }).catch(() => { models.value = []; });

function onNavigate(tab: TabId) {
  emit('navigate', tab);
}
</script>

<template>
  <section>
    <h2>Dashboard</h2>
    <p class="hint">Everything at a glance -- jump to a tool below, or check the watchlist for what moved.</p>

    <div class="stat-tile-row">
      <div class="stat-tile">
        <div class="stat-tile-label">Watchlist</div>
        <div class="stat-tile-value">{{ watchlist === null ? '…' : watchlist.length }}</div>
      </div>
      <div class="stat-tile">
        <div class="stat-tile-label">Simulation runs</div>
        <div class="stat-tile-value">{{ runs === null ? '…' : runs.length }}</div>
      </div>
      <div class="stat-tile">
        <div class="stat-tile-label">Trained models</div>
        <div class="stat-tile-value">{{ models === null ? '…' : models.length }}</div>
      </div>
    </div>

    <div class="quick-actions">
      <button type="button" @click="onNavigate('analyst')">Analyze a company</button>
      <button type="button" @click="onNavigate('terminal')">Open terminal</button>
      <button type="button" @click="onNavigate('watchlist')">Manage watchlist</button>
      <button type="button" @click="onNavigate('price')">Simulate a price</button>
    </div>

    <h3>Watchlist</h3>
    <p v-if="watchlist === null">Loading…</p>
    <p v-else-if="watchlist.length === 0" class="hint">
      Nothing saved yet -- add a ticker from the
      <a role="button" tabindex="0" @click="onNavigate('watchlist')">Watchlist tab</a>.
    </p>
    <div v-else class="table-scroll">
      <table class="data-table watchlist-table">
        <thead>
          <tr><th>Ticker</th><th>Price</th><th>Day change</th><th>30d</th><th>Quality</th><th>Risk</th></tr>
        </thead>
        <tbody>
          <tr v-for="row in watchlist" :key="row.ticker">
            <td>{{ row.ticker }}</td>
            <td>{{ fmtMoney(row.last_price) }}</td>
            <td :class="row.day_change_pct != null && row.day_change_pct >= 0 ? 'direction up' : 'direction down'">
              {{ fmtPct(row.day_change_pct) }}
            </td>
            <td>
              <Sparkline
                :values="row.sparkline"
                :positive="row.sparkline.length > 1 && row.sparkline[row.sparkline.length - 1] >= row.sparkline[0]"
              />
            </td>
            <td>{{ fmtScore(row.scores.business_quality) }}</td>
            <td>{{ row.scores.risk_label }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
