<script setup lang="ts">
import { ref } from 'vue';
import { api, ApiError } from '../api';
import ErrorBox from '../components/ErrorBox.vue';
import SubmitButton from '../components/SubmitButton.vue';
import { fmtScore } from '../format';
import type { FundamentalsCompareResponse } from '../types';

const tickers = ref('MU,WDC,STX');
const busy = ref(false);
const result = ref<FundamentalsCompareResponse | null>(null);
const error = ref<Error | null>(null);

async function onSubmit() {
  busy.value = true;
  error.value = null;
  result.value = null;
  try {
    const tickerList = tickers.value.split(',').map((t) => t.trim()).filter(Boolean);
    result.value = await api.fundamentalsCompare({ tickers: tickerList });
  } catch (err) {
    error.value = err instanceof ApiError ? err : new Error(String(err));
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <section>
    <h2>Compare companies</h2>
    <p class="hint">
      e.g. Micron vs Western Digital vs Seagate &mdash; ranked by a simple composite of quality, growth, financial
      strength, and valuation, minus a risk penalty.
    </p>
    <form class="run-form" @submit.prevent="onSubmit">
      <fieldset :disabled="busy" class="run-form-fields">
        <label>
          Tickers (comma-separated)
          <input v-model="tickers" required placeholder="MU,WDC,STX" />
        </label>
        <SubmitButton :busy="busy" busy-label="Analyzing…">Compare</SubmitButton>
      </fieldset>
    </form>
    <div class="result">
      <ErrorBox v-if="error" :error="error" />
      <template v-if="result">
        <div class="table-scroll">
          <table class="data-table">
            <thead>
              <tr>
                <th>Rank</th><th>Ticker</th><th>Company</th><th>Composite</th><th>Quality</th>
                <th>Growth</th><th>Fin. strength</th><th>Valuation</th><th>Risk</th>
                <th>Revenue</th><th>FCF</th><th>Debt</th><th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(r, i) in result.rows" :key="r.ticker">
                <td>{{ i + 1 }}</td>
                <td>{{ r.ticker }}</td>
                <td>{{ r.company_name }}</td>
                <td>{{ fmtScore(r.composite) }}</td>
                <td>{{ fmtScore(r.business_quality) }}</td>
                <td>{{ fmtScore(r.growth) }}</td>
                <td>{{ fmtScore(r.financial_strength) }}</td>
                <td>{{ fmtScore(r.valuation) }}</td>
                <td>{{ r.risk_label || 'n/a' }}</td>
                <td>{{ r.revenue_trend }}</td>
                <td>{{ r.fcf_status }}</td>
                <td>{{ r.debt_position }}</td>
                <td>{{ r.confidence }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
        <template v-if="Object.keys(result.errors).length > 0">
          <p class="error">Errors:</p>
          <ul class="error">
            <li v-for="[t, e] in Object.entries(result.errors)" :key="t">{{ t }}: {{ e }}</li>
          </ul>
        </template>
      </template>
    </div>
  </section>
</template>
