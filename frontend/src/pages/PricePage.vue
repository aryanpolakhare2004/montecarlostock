<script setup lang="ts">
import { ref } from 'vue';
import { api, ApiError } from '../api';
import StatTable from '../components/StatTable.vue';
import ErrorBox from '../components/ErrorBox.vue';
import ExportButtons from '../components/ExportButtons.vue';
import SubmitButton from '../components/SubmitButton.vue';
import FanChart from '../components/charts/FanChart.vue';
import Histogram from '../components/charts/Histogram.vue';
import { fmtMoney, fmtPct } from '../format';
import type { PriceResponse } from '../types';

const ticker = ref('AAPL');
const period = ref('5y');
const days = ref(252);
const sims = ref(10000);
const seed = ref('');
const busy = ref(false);
const result = ref<PriceResponse | null>(null);
const error = ref<Error | null>(null);

async function onSubmit() {
  busy.value = true;
  error.value = null;
  result.value = null;
  try {
    result.value = await api.price({
      ticker: ticker.value, period: period.value, days: days.value, sims: sims.value,
      seed: seed.value === '' ? null : Number(seed.value),
    });
  } catch (err) {
    error.value = err instanceof ApiError ? err : new Error(String(err));
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <section>
    <h2>Simulate future price paths (GBM)</h2>
    <form class="run-form" @submit.prevent="onSubmit">
      <fieldset :disabled="busy" class="run-form-fields">
        <label>
          Ticker
          <input v-model="ticker" required placeholder="AAPL" />
        </label>
        <details class="advanced-fields">
          <summary>Advanced options</summary>
          <div class="advanced-fields-grid">
            <label>
              Period
              <input v-model="period" />
            </label>
            <label>
              Days
              <input type="number" min="1" v-model.number="days" />
            </label>
            <label>
              Sims
              <input type="number" min="1" v-model.number="sims" />
            </label>
            <label>
              Seed
              <input v-model="seed" placeholder="optional" />
            </label>
          </div>
        </details>
        <SubmitButton :busy="busy">Run</SubmitButton>
      </fieldset>
    </form>
    <div class="result">
      <ErrorBox v-if="error" :error="error" />
      <template v-if="result">
        <p>
          s0={{ fmtMoney(result.s0) }} mu={{ fmtPct(result.mu) }}/yr sigma={{ fmtPct(result.sigma) }}/yr
        </p>
        <StatTable :summary="result.summary" />
        <ExportButtons :run-id="result.run_id" :csv-filename="`price_${ticker}_${result.run_id}.csv`" :csv-rows="result.bands" />
        <FanChart :data="result.bands" y-label="Price" />
        <Histogram :data="result.distribution" x-label="Final price" :reference-value="result.s0" />
      </template>
    </div>
  </section>
</template>
