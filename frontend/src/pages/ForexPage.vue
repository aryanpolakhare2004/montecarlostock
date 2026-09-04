<script setup lang="ts">
import { ref } from 'vue';
import { api } from '../api';
import ErrorBox from '../components/ErrorBox.vue';
import MarketOverviewTable from '../components/MarketOverviewTable.vue';
import AssetSimulate from '../components/AssetSimulate.vue';
import AssetBacktest from '../components/AssetBacktest.vue';
import type { MarketAsset, MarketAssetQuote } from '../types';

const forexList = ref<MarketAsset[] | null>(null);
const quotes = ref<MarketAssetQuote[] | null>(null);
const quoteErrors = ref<Record<string, string>>({});
const loadError = ref<Error | null>(null);
const symbol = ref('');

api.listForex().then((r) => {
  forexList.value = r.forex;
  if (r.forex.length > 0) symbol.value = r.forex[0].symbol;
}).catch((e) => { loadError.value = e; });
api.forexQuotes().then((r) => {
  quotes.value = r.quotes;
  quoteErrors.value = r.errors;
}).catch((e) => { loadError.value = e; });

function onSelect(s: string) {
  symbol.value = s;
}
</script>

<template>
  <section>
    <h2>Forex</h2>
    <p class="hint">
      A curated set of major currency pairs via the same Monte Carlo price simulation and strategy backtest used
      for stocks. No fundamentals data here -- currency pairs aren't companies.
    </p>

    <ErrorBox v-if="loadError" :error="loadError" />
    <p v-else-if="quotes === null">Loading…</p>
    <MarketOverviewTable v-else :quotes="quotes" :errors="quoteErrors" :selected-symbol="symbol" :on-select="onSelect" />

    <template v-if="forexList && forexList.length > 0">
      <label class="commodity-select-label">
        Currency pair
        <select v-model="symbol">
          <option v-for="c in forexList" :key="c.symbol" :value="c.symbol">{{ c.name }} ({{ c.symbol }})</option>
        </select>
      </label>

      <AssetSimulate :symbol="symbol" />
      <AssetBacktest :symbol="symbol" />
    </template>
  </section>
</template>
