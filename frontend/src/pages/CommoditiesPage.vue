<script setup lang="ts">
import { ref } from 'vue';
import { api } from '../api';
import ErrorBox from '../components/ErrorBox.vue';
import MarketOverviewTable from '../components/MarketOverviewTable.vue';
import AssetSimulate from '../components/AssetSimulate.vue';
import AssetBacktest from '../components/AssetBacktest.vue';
import type { MarketAsset, MarketAssetQuote } from '../types';

const commodityList = ref<MarketAsset[] | null>(null);
const quotes = ref<MarketAssetQuote[] | null>(null);
const quoteErrors = ref<Record<string, string>>({});
const loadError = ref<Error | null>(null);
const symbol = ref('');

api.listCommodities().then((r) => {
  commodityList.value = r.commodities;
  if (r.commodities.length > 0) symbol.value = r.commodities[0].symbol;
}).catch((e) => { loadError.value = e; });
api.commodityQuotes().then((r) => {
  quotes.value = r.quotes;
  quoteErrors.value = r.errors;
}).catch((e) => { loadError.value = e; });

function onSelect(s: string) {
  symbol.value = s;
}
</script>

<template>
  <section>
    <h2>Commodities</h2>
    <p class="hint">
      A curated set of commodity futures (metals, energy, agriculture) via the same Monte Carlo price simulation
      and strategy backtest used for stocks. No fundamentals data here -- futures don't have SEC filings.
    </p>

    <ErrorBox v-if="loadError" :error="loadError" />
    <p v-else-if="quotes === null">Loading…</p>
    <MarketOverviewTable v-else :quotes="quotes" :errors="quoteErrors" :selected-symbol="symbol" :on-select="onSelect" />

    <template v-if="commodityList && commodityList.length > 0">
      <label class="commodity-select-label">
        Commodity
        <select v-model="symbol">
          <option v-for="c in commodityList" :key="c.symbol" :value="c.symbol">{{ c.name }} ({{ c.symbol }})</option>
        </select>
      </label>

      <AssetSimulate :symbol="symbol" />
      <AssetBacktest :symbol="symbol" />
    </template>
  </section>
</template>
