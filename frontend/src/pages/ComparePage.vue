<script setup lang="ts">
import { ref } from 'vue';
import { api, ApiError } from '../api';
import ErrorBox from '../components/ErrorBox.vue';
import ExportButtons from '../components/ExportButtons.vue';
import SubmitButton from '../components/SubmitButton.vue';
import CategoricalBarChart from '../components/charts/CategoricalBarChart.vue';
import type { useModels } from '../composables/useModels';
import type { CompareResponse } from '../types';

type ModelOptions = ReturnType<typeof useModels>;
defineProps<{ modelOptions: ModelOptions }>();

const ticker = ref('AAPL');
const period = ref('5y');
const days = ref(252);
const sims = ref(5000);
const blockSize = ref(5);
const fast = ref(20);
const slow = ref(50);
const rsiPeriod = ref(14);
const oversold = ref(30);
const overbought = ref(70);
const seed = ref('');
const modelIds = ref<number[]>([]);
const busy = ref(false);
const result = ref<CompareResponse | null>(null);
const error = ref<Error | null>(null);

function fmtPct1(v: number): string {
  return `${(v * 100).toFixed(1)}%`;
}

async function onSubmit() {
  error.value = null;
  if (oversold.value >= overbought.value) {
    error.value = new Error('Oversold threshold must be smaller than overbought threshold');
    return;
  }
  busy.value = true;
  result.value = null;
  try {
    result.value = await api.compare({
      ticker: ticker.value, period: period.value, days: days.value, sims: sims.value, block_size: blockSize.value,
      fast: fast.value, slow: slow.value, rsi_period: rsiPeriod.value, oversold: oversold.value, overbought: overbought.value,
      seed: seed.value === '' ? null : Number(seed.value),
      model_ids: modelIds.value,
    });
  } catch (err) {
    error.value = err instanceof ApiError ? err : new Error(String(err));
  } finally {
    busy.value = false;
  }
}

function csvRows() {
  if (!result.value) return [];
  return result.value.ranking.map((name, i) => ({ rank: i + 1, strategy: name, ...result.value!.results[name] }));
}

function chartData() {
  if (!result.value) return [];
  return result.value.ranking.map((name) => {
    const s = result.value!.results[name];
    return {
      name,
      value: s.mean_return,
      extra: [
        { label: 'std return', value: s.std_return.toFixed(4) },
        { label: 'prob profit', value: s.prob_profit.toFixed(3) },
        { label: 'mean max drawdown', value: s.mean_max_drawdown.toFixed(4) },
      ],
    };
  });
}
</script>

<template>
  <section>
    <h2>Compare algorithms on one stock</h2>
    <p class="hint">
      Runs buy-and-hold, sma-crossover, mean-reversion, and any trained <code>ml-technical</code>-eligible models
      (technical-only: sentiment none, volume unchecked) on the <em>same</em> resampled price paths, so the
      ranking reflects strategy skill, not lucky scenarios.
    </p>
    <form class="run-form" @submit.prevent="onSubmit">
      <fieldset :disabled="busy" class="run-form-fields">
        <label>
          Ticker
          <input v-model="ticker" required placeholder="AAPL" />
        </label>
        <label>
          Include ML models
          <select multiple size="4" v-model="modelIds">
            <option v-for="m in modelOptions.technicalOnly" :key="m.id" :value="m.id">
              #{{ m.id }} {{ m.ticker }} {{ m.model_type }} (test acc {{ m.test_accuracy.toFixed(2) }})
            </option>
          </select>
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
              Block size
              <input type="number" min="1" v-model.number="blockSize" />
            </label>
            <label>
              Fast SMA
              <input type="number" min="1" v-model.number="fast" />
            </label>
            <label>
              Slow SMA
              <input type="number" min="1" v-model.number="slow" />
            </label>
            <label>
              RSI period
              <input type="number" min="1" v-model.number="rsiPeriod" />
            </label>
            <label>
              Oversold
              <input type="number" min="0" max="100" v-model.number="oversold" />
            </label>
            <label>
              Overbought
              <input type="number" min="0" max="100" v-model.number="overbought" />
            </label>
            <label>
              Seed
              <input v-model="seed" placeholder="optional" />
            </label>
          </div>
        </details>
        <SubmitButton :busy="busy">Compare</SubmitButton>
      </fieldset>
    </form>
    <div class="result">
      <ErrorBox v-if="error" :error="error" />
      <template v-if="result">
        <ExportButtons
          :run-id="result.run_id"
          :csv-filename="`compare_${ticker}_${result.run_id}.csv`"
          :csv-rows="csvRows()"
        />
        <div class="table-scroll">
          <table class="data-table">
            <thead>
              <tr>
                <th>Rank</th><th>Strategy</th><th>Mean return</th><th>Std return</th>
                <th>Prob profit</th><th>Mean max drawdown</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(name, i) in result.ranking" :key="name">
                <td>{{ i + 1 }}</td>
                <td>{{ name }}</td>
                <td>{{ result.results[name].mean_return.toFixed(4) }}</td>
                <td>{{ result.results[name].std_return.toFixed(4) }}</td>
                <td>{{ result.results[name].prob_profit.toFixed(3) }}</td>
                <td>{{ result.results[name].mean_max_drawdown.toFixed(4) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <CategoricalBarChart y-label="Mean return" :format-value="fmtPct1" :data="chartData()" />
      </template>
    </div>
  </section>
</template>
