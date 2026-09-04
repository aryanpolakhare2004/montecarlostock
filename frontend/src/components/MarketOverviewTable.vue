<script setup lang="ts">
import Sparkline from './Sparkline.vue';
import { fmtMoney, fmtPct } from '../format';
import type { MarketAssetQuote } from '../types';

defineProps<{
  quotes: MarketAssetQuote[];
  errors: Record<string, string>;
  selectedSymbol: string;
  onSelect: (symbol: string) => void;
}>();
</script>

<template>
  <div v-if="quotes.length > 0" class="table-scroll">
    <table class="data-table watchlist-table">
      <thead>
        <tr><th>Name</th><th>Symbol</th><th>Price</th><th>Day change</th><th>30d</th></tr>
      </thead>
      <tbody>
        <tr
          v-for="q in quotes"
          :key="q.symbol"
          :class="q.symbol === selectedSymbol ? 'selected-row' : undefined"
          style="cursor: pointer"
          @click="onSelect(q.symbol)"
        >
          <td>{{ q.name }}</td>
          <td>{{ q.symbol }}</td>
          <td>{{ fmtMoney(q.last_price) }}</td>
          <td :class="q.day_change_pct != null && q.day_change_pct >= 0 ? 'direction up' : 'direction down'">
            {{ fmtPct(q.day_change_pct) }}
          </td>
          <td>
            <Sparkline
              :values="q.sparkline"
              :positive="q.sparkline.length > 1 && q.sparkline[q.sparkline.length - 1] >= q.sparkline[0]"
            />
          </td>
        </tr>
      </tbody>
    </table>
  </div>
  <template v-if="Object.keys(errors).length > 0">
    <p class="error">Errors:</p>
    <ul class="error">
      <li v-for="[sym, e] in Object.entries(errors)" :key="sym">{{ sym }}: {{ e }}</li>
    </ul>
  </template>
</template>
