<script setup lang="ts">
import { ref } from 'vue';
import { api, ApiError } from '../api';
import StatTable from './StatTable.vue';
import ErrorBox from './ErrorBox.vue';
import ExportButtons from './ExportButtons.vue';
import SubmitButton from './SubmitButton.vue';
import Histogram from './charts/Histogram.vue';
import type { StrategyRequest, StrategyResponse } from '../types';

const props = defineProps<{ symbol: string }>();

const strategy = ref<'buy-and-hold' | 'sma-crossover' | 'mean-reversion'>('buy-and-hold');
const fast = ref(20);
const slow = ref(50);
const rsiPeriod = ref(14);
const oversold = ref(30);
const overbought = ref(70);
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
      ticker: props.symbol,
      strategy: strategy.value as StrategyRequest['strategy'],
      fast: fast.value, slow: slow.value, rsi_period: rsiPeriod.value, oversold: oversold.value, overbought: overbought.value,
      period: period.value, days: days.value, sims: sims.value, block_size: blockSize.value,
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
  <div class="commodity-block">
    <h3>Backtest a strategy</h3>
    <form class="run-form" @submit.prevent="onSubmit">
      <fieldset :disabled="busy" class="run-form-fields">
        <label>
          Strategy
          <select v-model="strategy">
            <option value="buy-and-hold">buy-and-hold</option>
            <option value="sma-crossover">sma-crossover</option>
            <option value="mean-reversion">mean-reversion</option>
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
        <ExportButtons :run-id="result.run_id" :csv-filename="`strategy_${symbol}_${result.run_id}.csv`" :csv-rows="result.distribution" />
        <Histogram
          :data="result.distribution" x-label="Total return" :reference-value="0"
          :format-value="fmtPct1"
        />
      </template>
    </div>
  </div>
</template>
