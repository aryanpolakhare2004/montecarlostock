<script setup lang="ts">
import { ref } from 'vue';
import { api, ApiError } from '../api';
import StatTable from '../components/StatTable.vue';
import ErrorBox from '../components/ErrorBox.vue';
import ExportButtons from '../components/ExportButtons.vue';
import SubmitButton from '../components/SubmitButton.vue';
import Histogram from '../components/charts/Histogram.vue';
import type { useModels } from '../composables/useModels';
import type { StrategyRequest, StrategyResponse } from '../types';

type ModelOptions = ReturnType<typeof useModels>;
defineProps<{ modelOptions: ModelOptions }>();

const ticker = ref('AAPL');
const strategy = ref<StrategyRequest['strategy']>('buy-and-hold');
const fast = ref(20);
const slow = ref(50);
const rsiPeriod = ref(14);
const oversold = ref(30);
const overbought = ref(70);
const modelId = ref('');
const period = ref('5y');
const days = ref(252);
const sims = ref(5000);
const blockSize = ref(5);
const seed = ref('');
const busy = ref(false);
const result = ref<StrategyResponse | null>(null);
const error = ref<Error | null>(null);

function fmtPct1(v: number): string {
  return `${(v * 100).toFixed(1)}%`;
}

async function onSubmit() {
  error.value = null;
  if (strategy.value === 'mean-reversion' && oversold.value >= overbought.value) {
    error.value = new Error('Oversold threshold must be smaller than overbought threshold');
    return;
  }
  busy.value = true;
  result.value = null;
  try {
    result.value = await api.strategy({
      ticker: ticker.value,
      strategy: strategy.value,
      fast: fast.value, slow: slow.value, rsi_period: rsiPeriod.value, oversold: oversold.value, overbought: overbought.value,
      period: period.value, days: days.value, sims: sims.value, block_size: blockSize.value,
      seed: seed.value === '' ? null : Number(seed.value),
      model_id: modelId.value ? Number(modelId.value) : null,
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
    <h2>Monte Carlo backtest a trading strategy</h2>
    <form class="run-form" @submit.prevent="onSubmit">
      <fieldset :disabled="busy" class="run-form-fields">
        <label>
          Ticker
          <input v-model="ticker" required placeholder="AAPL" />
        </label>
        <label>
          Strategy
          <select v-model="strategy">
            <option value="buy-and-hold">buy-and-hold</option>
            <option value="sma-crossover">sma-crossover</option>
            <option value="mean-reversion">mean-reversion</option>
            <option value="ml-technical">ml-technical</option>
          </select>
        </label>
        <template v-if="strategy === 'sma-crossover'">
          <label>
            Fast SMA
            <input type="number" min="1" v-model.number="fast" />
          </label>
          <label>
            Slow SMA
            <input type="number" min="1" v-model.number="slow" />
          </label>
        </template>
        <template v-if="strategy === 'mean-reversion'">
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
        </template>
        <label v-if="strategy === 'ml-technical'">
          Model
          <select v-model="modelId">
            <option value="">(load models first)</option>
            <option v-for="m in modelOptions.technicalOnly" :key="m.id" :value="String(m.id)">
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
        <StatTable :summary="result.summary" />
        <ExportButtons :run-id="result.run_id" :csv-filename="`strategy_${ticker}_${result.run_id}.csv`" :csv-rows="result.distribution" />
        <Histogram
          :data="result.distribution" x-label="Total return" :reference-value="0"
          :format-value="fmtPct1"
        />
      </template>
    </div>
  </section>
</template>
