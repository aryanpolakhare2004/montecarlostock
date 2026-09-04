<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue';
import { api, ApiError } from '../api';
import ErrorBox from '../components/ErrorBox.vue';
import Sparkline from '../components/Sparkline.vue';
import SubmitButton from '../components/SubmitButton.vue';
import { useToast } from '../composables/useToast';
import { fmtMoney, fmtPct, fmtScore } from '../format';
import { parseCsvTickerColumn, parseTickerListText } from '../utils/tickers';
import type { Alert, WatchlistResponse } from '../types';

const ALERT_POLL_MS = 60_000;

const data = ref<WatchlistResponse | null>(null);
const loadError = ref<Error | null>(null);
const newTicker = ref('');
const busy = ref(false);
const addError = ref<Error | null>(null);
const alerts = ref<Alert[]>([]);
const alertFormTicker = ref<string | null>(null);
const alertMetric = ref<Alert['metric']>('price');
const alertOperator = ref<Alert['operator']>('above');
const alertThreshold = ref('');
const bulkText = ref('');
const importing = ref(false);
const fileInputRef = ref<HTMLInputElement | null>(null);
const { showToast } = useToast();

const seenTriggeredIds = new Set<number>();
let alertsInitialized = false;
let pollInterval: ReturnType<typeof setInterval> | undefined;

function load() {
  loadError.value = null;
  api.listWatchlist().then((r) => { data.value = r; }).catch((e) => { loadError.value = e; });
}

function loadAlerts() {
  api.listAlerts().then((next) => {
    for (const alert of next) {
      if (alert.triggered_at) {
        if (!seenTriggeredIds.has(alert.id) && alertsInitialized) {
          showToast(`${alert.ticker}: ${alert.metric} ${alert.operator} ${alert.threshold} triggered`, 'info');
        }
        seenTriggeredIds.add(alert.id);
      }
    }
    alertsInitialized = true;
    alerts.value = next;
  }).catch(() => {});
}

onMounted(() => {
  load();
  loadAlerts();
  pollInterval = setInterval(loadAlerts, ALERT_POLL_MS);
});

onUnmounted(() => {
  clearInterval(pollInterval);
});

async function onAdd() {
  if (!newTicker.value.trim()) return;
  busy.value = true;
  addError.value = null;
  try {
    const added = await api.addWatchlist(newTicker.value.trim());
    newTicker.value = '';
    load();
    showToast(`Added ${added.ticker} to watchlist`, 'success');
  } catch (err) {
    const error = err instanceof ApiError ? err : new Error(String(err));
    addError.value = error;
    showToast(`Couldn't add ${newTicker.value.trim().toUpperCase()}: ${error.message}`, 'error');
  } finally {
    busy.value = false;
  }
}

function onFileSelected(evt: Event) {
  const input = evt.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = '';
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    const content = typeof reader.result === 'string' ? reader.result : '';
    const csvTickers = parseCsvTickerColumn(content);
    if (csvTickers.length === 0) {
      showToast('No tickers found in that file', 'error');
      return;
    }
    const existing = bulkText.value.trim();
    bulkText.value = existing ? `${existing}, ${csvTickers.join(', ')}` : csvTickers.join(', ');
  };
  reader.readAsText(file);
}

async function onImport() {
  const tickerList = parseTickerListText(bulkText.value);
  if (tickerList.length === 0) {
    showToast('No valid tickers found to import', 'error');
    return;
  }
  importing.value = true;
  try {
    const response = await api.bulkAddWatchlist(tickerList);
    bulkText.value = '';
    load();
    const failCount = Object.keys(response.errors).length;
    const message = failCount > 0
      ? `Imported ${response.added.length} tickers, ${failCount} failed (${Object.keys(response.errors).join(', ')})`
      : `Imported ${response.added.length} tickers`;
    showToast(message, failCount > 0 ? 'info' : 'success');
  } catch (err) {
    const error = err instanceof ApiError ? err : new Error(String(err));
    showToast(`Import failed: ${error.message}`, 'error');
  } finally {
    importing.value = false;
  }
}

async function onRemove(ticker: string) {
  await api.removeWatchlist(ticker);
  load();
  showToast(`Removed ${ticker} from watchlist`, 'info');
}

function alertsFor(ticker: string): Alert[] {
  return alerts.value.filter((a) => a.ticker === ticker);
}

function openAlertForm(ticker: string) {
  alertFormTicker.value = ticker;
  alertMetric.value = 'price';
  alertOperator.value = 'above';
  alertThreshold.value = '';
}

async function onAddAlert(ticker: string) {
  if (!alertThreshold.value.trim()) return;
  try {
    await api.addAlert({
      ticker, metric: alertMetric.value, operator: alertOperator.value, threshold: Number(alertThreshold.value),
    });
    alertFormTicker.value = null;
    loadAlerts();
    showToast(`Alert added for ${ticker}`, 'success');
  } catch (err) {
    const error = err instanceof ApiError ? err : new Error(String(err));
    showToast(`Couldn't add alert: ${error.message}`, 'error');
  }
}

async function onRemoveAlert(id: number) {
  await api.removeAlert(id);
  loadAlerts();
}
</script>

<template>
  <section>
    <h2>Watchlist</h2>
    <p class="hint">
      Quick glance across the tickers you follow: last price, day change, a 30-day sparkline, the same
      quality/growth/financial-strength/valuation scorecard as the Analyst tab (computed from cached SEC data,
      so repeat visits load fast), and price/volatility alerts checked in the background.
    </p>

    <form class="run-form" @submit.prevent="onAdd">
      <fieldset :disabled="busy" class="run-form-fields">
        <label>
          Add ticker
          <input v-model="newTicker" placeholder="AAPL" />
        </label>
        <SubmitButton :busy="busy">Add</SubmitButton>
      </fieldset>
    </form>
    <ErrorBox v-if="addError" :error="addError" />

    <details class="advanced-fields">
      <summary>Bulk import (paste or upload CSV)</summary>
      <div class="advanced-fields-grid bulk-import">
        <textarea
          class="bulk-import-textarea"
          v-model="bulkText"
          placeholder="Paste tickers separated by commas or one per line -- CSV works too (first column is used)&#10;AAPL, MSFT, GOOG"
          rows="5"
        />
        <div class="bulk-import-actions">
          <input
            ref="fileInputRef"
            type="file"
            accept=".csv,text/csv"
            style="display: none"
            @change="onFileSelected"
          />
          <button type="button" class="refresh-btn" @click="fileInputRef?.click()">Upload CSV</button>
          <button type="button" class="refresh-btn" :disabled="importing" @click="onImport">
            {{ importing ? 'Importing…' : 'Import' }}
          </button>
        </div>
      </div>
    </details>

    <div class="result">
      <ErrorBox v-if="loadError" :error="loadError" />
      <template v-else-if="data">
        <p v-if="data.tickers.length === 0" class="hint">No tickers yet -- add one above.</p>
        <div v-else class="table-scroll">
          <table class="data-table watchlist-table">
            <thead>
              <tr>
                <th>Ticker</th><th>Company</th><th>Price</th><th>Day change</th><th>30d</th>
                <th>Quality</th><th>Growth</th><th>Fin. strength</th><th>Valuation</th><th>Risk</th>
                <th>Alerts</th><th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in data.tickers" :key="row.ticker">
                <td>{{ row.ticker }}</td>
                <td>{{ row.company_name }}</td>
                <td>{{ fmtMoney(row.last_price) }}</td>
                <td :class="row.day_change_pct != null && row.day_change_pct >= 0 ? 'direction up' : 'direction down'">
                  {{ fmtPct(row.day_change_pct) }}
                </td>
                <td>
                  <Sparkline
                    :values="row.sparkline"
                    :positive="row.sparkline.length > 1 && row.sparkline[row.sparkline.length - 1] >= row.sparkline[0]"
                  />
                </td>
                <td>{{ fmtScore(row.scores.business_quality) }}</td>
                <td>{{ fmtScore(row.scores.growth) }}</td>
                <td>{{ fmtScore(row.scores.financial_strength) }}</td>
                <td>{{ fmtScore(row.scores.valuation) }}</td>
                <td>{{ row.scores.risk_label }}</td>
                <td>
                  <div class="alert-cell">
                    <span v-for="a in alertsFor(row.ticker)" :key="a.id" :class="`alert-chip${a.triggered_at ? ' triggered' : ''}`">
                      {{ a.metric }} {{ a.operator === 'above' ? '>' : '<' }} {{ a.threshold }}
                      <button type="button" aria-label="Remove alert" @click="onRemoveAlert(a.id)">×</button>
                    </span>
                    <form v-if="alertFormTicker === row.ticker" class="alert-form" @submit.prevent="onAddAlert(row.ticker)">
                      <select v-model="alertMetric">
                        <option value="price">Price</option>
                        <option value="volatility">Volatility</option>
                      </select>
                      <select v-model="alertOperator">
                        <option value="above">above</option>
                        <option value="below">below</option>
                      </select>
                      <input type="number" step="any" v-model="alertThreshold" placeholder="threshold" required />
                      <button type="submit">Add</button>
                      <button type="button" @click="alertFormTicker = null">Cancel</button>
                    </form>
                    <button v-else type="button" class="refresh-btn" @click="openAlertForm(row.ticker)">+ alert</button>
                  </div>
                </td>
                <td>
                  <button type="button" class="refresh-btn" @click="onRemove(row.ticker)">remove</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <template v-if="Object.keys(data.errors).length > 0">
          <p class="error">Errors:</p>
          <ul class="error">
            <li v-for="[t, e] in Object.entries(data.errors)" :key="t">{{ t }}: {{ e }}</li>
          </ul>
        </template>
      </template>
      <p v-else>Loading…</p>
    </div>
  </section>
</template>
