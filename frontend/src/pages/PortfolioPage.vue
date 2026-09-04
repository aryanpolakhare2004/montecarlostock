<script setup lang="ts">
import { ref } from 'vue';
import { api, ApiError } from '../api';
import StatTable from '../components/StatTable.vue';
import ErrorBox from '../components/ErrorBox.vue';
import ExportButtons from '../components/ExportButtons.vue';
import SubmitButton from '../components/SubmitButton.vue';
import { useToast } from '../composables/useToast';
import FanChart from '../components/charts/FanChart.vue';
import { fmtPct } from '../format';
import type { PortfolioCorrelationResponse, PortfolioOptimizeRequest, PortfolioResponse } from '../types';

function corrClass(v: number): string {
  if (v <= -0.5) return 'corr-strong-neg';
  if (v <= -0.1) return 'corr-weak-neg';
  if (v < 0.1) return 'corr-neutral';
  if (v < 0.5) return 'corr-weak-pos';
  return 'corr-strong-pos';
}

const tickers = ref('AAPL,MSFT,GOOG');
const weights = ref('');
const objective = ref<PortfolioOptimizeRequest['objective']>('max_sharpe');
const riskFreeRate = ref(0);
const optimizing = ref(false);
const correlating = ref(false);
const correlation = ref<PortfolioCorrelationResponse | null>(null);
const value = ref(10000);
const period = ref('5y');
const days = ref(252);
const sims = ref(5000);
const seed = ref('');
const busy = ref(false);
const result = ref<PortfolioResponse | null>(null);
const error = ref<Error | null>(null);
const { showToast } = useToast();

function parsedTickers(): string[] {
  return tickers.value.split(',').map((t) => t.trim()).filter(Boolean);
}

async function onOptimize() {
  const tickerList = parsedTickers();
  if (tickerList.length < 2) {
    showToast('Enter at least two tickers to optimize weights', 'error');
    return;
  }
  optimizing.value = true;
  try {
    const response = await api.optimizePortfolio({
      tickers: tickerList, period: period.value, objective: objective.value, risk_free_rate: riskFreeRate.value,
    });
    weights.value = tickerList.map((t) => response.weights[t].toFixed(3)).join(',');
    const sharpeText = response.sharpe_ratio != null ? response.sharpe_ratio.toFixed(2) : 'n/a';
    showToast(
      `Optimized: expected return ${fmtPct(response.expected_return)}, ` +
        `volatility ${fmtPct(response.expected_volatility)}, Sharpe ${sharpeText}`,
      'success',
    );
  } catch (err) {
    const errorObj = err instanceof ApiError ? err : new Error(String(err));
    showToast(`Optimization failed: ${errorObj.message}`, 'error');
  } finally {
    optimizing.value = false;
  }
}

async function onCorrelate() {
  const tickerList = parsedTickers();
  if (tickerList.length < 2) {
    showToast('Enter at least two tickers to show correlation', 'error');
    return;
  }
  correlating.value = true;
  try {
    correlation.value = await api.portfolioCorrelation({ tickers: tickerList, period: period.value });
  } catch (err) {
    const errorObj = err instanceof ApiError ? err : new Error(String(err));
    showToast(`Correlation failed: ${errorObj.message}`, 'error');
  } finally {
    correlating.value = false;
  }
}

async function onSubmit() {
  busy.value = true;
  error.value = null;
  result.value = null;
  try {
    const tickerList = parsedTickers();
    const weightList = weights.value
      ? weights.value.split(',').map((w) => Number(w.trim())).filter((w) => !Number.isNaN(w))
      : null;
    result.value = await api.portfolio({
      tickers: tickerList, weights: weightList, value: value.value, period: period.value, days: days.value,
      sims: sims.value, seed: seed.value === '' ? null : Number(seed.value),
    });
  } catch (err) {
    error.value = err instanceof ApiError ? err : new Error(String(err));
  } finally {
    busy.value = false;
  }
}

function resultWeightsText(): string {
  if (!result.value) return '';
  return Object.entries(result.value.weights).map(([t, w]) => `${t}: ${w.toFixed(3)}`).join(', ');
}
</script>

<template>
  <section>
    <h2>Simulate a multi-asset portfolio</h2>
    <form class="run-form" @submit.prevent="onSubmit">
      <fieldset :disabled="busy" class="run-form-fields">
        <label>
          Tickers (comma-separated)
          <input v-model="tickers" required placeholder="AAPL,MSFT,GOOG" />
        </label>
        <label>
          Weights (comma-separated, optional)
          <input v-model="weights" placeholder="0.5,0.3,0.2" />
        </label>
        <label>
          Optimize for
          <select v-model="objective">
            <option value="max_sharpe">max Sharpe ratio</option>
            <option value="min_variance">min variance</option>
          </select>
        </label>
        <label>
          Risk-free rate
          <input type="number" step="0.01" v-model.number="riskFreeRate" />
        </label>
        <button type="button" class="refresh-btn" :disabled="optimizing" @click="onOptimize">
          {{ optimizing ? 'Optimizing…' : 'Optimize weights' }}
        </button>
        <button type="button" class="refresh-btn" :disabled="correlating" @click="onCorrelate">
          {{ correlating ? 'Loading…' : 'Show correlation' }}
        </button>
        <label>
          Starting value
          <input type="number" min="0" v-model.number="value" />
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
    <div v-if="correlation" class="table-scroll">
      <table class="data-table corr-table">
        <thead>
          <tr><th></th><th v-for="t in correlation.tickers" :key="t">{{ t }}</th></tr>
        </thead>
        <tbody>
          <tr v-for="(rowTicker, i) in correlation.tickers" :key="rowTicker">
            <th>{{ rowTicker }}</th>
            <td
              v-for="(colTicker, j) in correlation.tickers" :key="colTicker"
              :class="i === j ? 'corr-diagonal' : corrClass(correlation.matrix[i][j])"
            >
              {{ correlation.matrix[i][j].toFixed(2) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="result">
      <ErrorBox v-if="error" :error="error" />
      <template v-if="result">
        <p>{{ resultWeightsText() }}</p>
        <StatTable :summary="result.summary" />
        <ExportButtons :run-id="result.run_id" :csv-filename="`portfolio_${result.run_id}.csv`" :csv-rows="result.bands" />
        <FanChart :data="result.bands" y-label="Portfolio value" />
      </template>
    </div>
  </section>
</template>
