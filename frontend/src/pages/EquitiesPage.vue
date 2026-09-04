<script setup lang="ts">
import { ref } from 'vue';
import { api } from '../api';
import ErrorBox from '../components/ErrorBox.vue';
import MarketOverviewTable from '../components/MarketOverviewTable.vue';
import AssetSimulate from '../components/AssetSimulate.vue';
import AssetBacktest from '../components/AssetBacktest.vue';
import { fmtMoney, fmtPct } from '../format';
import type { EquitySuggestion, MarketAsset, MarketAssetQuote } from '../types';

const equityList = ref<MarketAsset[] | null>(null);
const quotes = ref<MarketAssetQuote[] | null>(null);
const quoteErrors = ref<Record<string, string>>({});
const loadError = ref<Error | null>(null);
const symbol = ref('');

const suggestions = ref<EquitySuggestion[] | null>(null);
const suggestionErrors = ref<Record<string, string>>({});
const suggestionsError = ref<Error | null>(null);

api.listEquities().then((r) => {
  equityList.value = r.equities;
  if (r.equities.length > 0) symbol.value = r.equities[0].symbol;
}).catch((e) => { loadError.value = e; });
api.equityQuotes().then((r) => {
  quotes.value = r.quotes;
  quoteErrors.value = r.errors;
}).catch((e) => { loadError.value = e; });
api.equitySuggestions().then((r) => {
  suggestions.value = r.suggestions;
  suggestionErrors.value = r.errors;
}).catch((e) => { suggestionsError.value = e; });

function onSelect(s: string) {
  symbol.value = s;
}
</script>

<template>
  <section>
    <h2>Equities</h2>
    <p class="hint">
      A curated set of major, liquid stocks across sectors via the same Monte Carlo price simulation and strategy
      backtest used elsewhere. For fundamentals (SEC filings, financials) on any of these, use the Analyst or Price
      pages with the ticker.
    </p>

    <ErrorBox v-if="loadError" :error="loadError" />
    <p v-else-if="quotes === null">Loading…</p>
    <MarketOverviewTable v-else :quotes="quotes" :errors="quoteErrors" :selected-symbol="symbol" :on-select="onSelect" />

    <h3>Suggestions</h3>
    <p class="hint">
      Ranks this list by each symbol's own simulated GBM expected return -- projecting its historical drift and
      volatility forward, not a recommendation or a forecast. High-sigma names can rank well on a wide, uncertain
      distribution just as easily as a steady one; check "5th-95th percentile" before reading too much into rank.
    </p>
    <ErrorBox v-if="suggestionsError" :error="suggestionsError" />
    <p v-else-if="suggestions === null">Loading…</p>
    <div v-else-if="suggestions.length > 0" class="table-scroll">
      <table class="data-table watchlist-table">
        <thead>
          <tr>
            <th>#</th><th>Name</th><th>Symbol</th><th>Price</th>
            <th>Expected return</th><th>Prob. above start</th><th>5th-95th percentile</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(s, i) in suggestions" :key="s.symbol"
            :class="s.symbol === symbol ? 'selected-row' : undefined"
            style="cursor: pointer"
            @click="onSelect(s.symbol)"
          >
            <td>{{ i + 1 }}</td>
            <td>{{ s.name }}</td>
            <td>{{ s.symbol }}</td>
            <td>{{ fmtMoney(s.s0) }}</td>
            <td :class="s.expected_return_pct >= 0 ? 'direction up' : 'direction down'">
              {{ fmtPct(s.expected_return_pct) }}
            </td>
            <td>{{ fmtPct(s.prob_above_start) }}</td>
            <td>{{ fmtMoney(s.p05) }} - {{ fmtMoney(s.p95) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <template v-if="Object.keys(suggestionErrors).length > 0">
      <p class="error">Errors:</p>
      <ul class="error">
        <li v-for="[sym, e] in Object.entries(suggestionErrors)" :key="sym">{{ sym }}: {{ e }}</li>
      </ul>
    </template>

    <template v-if="equityList && equityList.length > 0">
      <label class="commodity-select-label">
        Equity
        <select v-model="symbol">
          <option v-for="c in equityList" :key="c.symbol" :value="c.symbol">{{ c.name }} ({{ c.symbol }})</option>
        </select>
      </label>

      <AssetSimulate :symbol="symbol" />
      <AssetBacktest :symbol="symbol" />
    </template>
  </section>
</template>
