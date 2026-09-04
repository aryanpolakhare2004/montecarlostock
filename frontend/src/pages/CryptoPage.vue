<script setup lang="ts">
import { ref } from 'vue';
import { api } from '../api';
import ErrorBox from '../components/ErrorBox.vue';
import MarketOverviewTable from '../components/MarketOverviewTable.vue';
import AssetSimulate from '../components/AssetSimulate.vue';
import AssetBacktest from '../components/AssetBacktest.vue';
import type { MarketAsset, MarketAssetQuote } from '../types';

const cryptoList = ref<MarketAsset[] | null>(null);
const quotes = ref<MarketAssetQuote[] | null>(null);
const quoteErrors = ref<Record<string, string>>({});
const loadError = ref<Error | null>(null);
const symbol = ref('');

api.listCrypto().then((r) => {
  cryptoList.value = r.crypto;
  if (r.crypto.length > 0) symbol.value = r.crypto[0].symbol;
}).catch((e) => { loadError.value = e; });
api.cryptoQuotes().then((r) => {
  quotes.value = r.quotes;
  quoteErrors.value = r.errors;
}).catch((e) => { loadError.value = e; });

function onSelect(s: string) {
  symbol.value = s;
}
</script>

<template>
  <section>
    <h2>Crypto</h2>
    <p class="hint">
      A curated set of cryptocurrencies via the same Monte Carlo price simulation and strategy backtest used for
      stocks. No fundamentals data here -- these aren't companies.
    </p>

    <ErrorBox v-if="loadError" :error="loadError" />
    <p v-else-if="quotes === null">Loading…</p>
    <MarketOverviewTable v-else :quotes="quotes" :errors="quoteErrors" :selected-symbol="symbol" :on-select="onSelect" />

    <template v-if="cryptoList && cryptoList.length > 0">
      <label class="commodity-select-label">
        Crypto asset
        <select v-model="symbol">
          <option v-for="c in cryptoList" :key="c.symbol" :value="c.symbol">{{ c.name }} ({{ c.symbol }})</option>
        </select>
      </label>

      <AssetSimulate :symbol="symbol" />
      <AssetBacktest :symbol="symbol" />
    </template>
  </section>
</template>
