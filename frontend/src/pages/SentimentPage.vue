<script setup lang="ts">
import { ref } from 'vue';
import { api, ApiError } from '../api';
import ErrorBox from '../components/ErrorBox.vue';
import SubmitButton from '../components/SubmitButton.vue';
import type { SentimentRequest, SentimentResponse } from '../types';

function fmtSentiment(v: number): string {
  return v >= 0 ? `+${v.toFixed(3)}` : v.toFixed(3);
}

function directionClass(v: number): string {
  return v >= 0 ? 'direction up' : 'direction down';
}

const ticker = ref('AAPL');
const sourceGroup = ref<NonNullable<SentimentRequest['source_group']>>('all');
const busy = ref(false);
const result = ref<SentimentResponse | null>(null);
const error = ref<Error | null>(null);

async function onSubmit() {
  busy.value = true;
  error.value = null;
  result.value = null;
  try {
    result.value = await api.sentiment({ ticker: ticker.value, source_group: sourceGroup.value });
  } catch (err) {
    error.value = err instanceof ApiError ? err : new Error(String(err));
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <section>
    <h2>News &amp; social sentiment</h2>
    <p class="hint">
      Scores recent headlines with VADER sentiment analysis, per source and aggregated by day. The same source
      groups used for ML training features (yfinance needs no key; RSS is free; Reddit needs
      <code> REDDIT_CLIENT_ID</code>/<code>REDDIT_CLIENT_SECRET</code>).
    </p>
    <form class="run-form" @submit.prevent="onSubmit">
      <fieldset :disabled="busy" class="run-form-fields">
        <label>
          Ticker
          <input v-model="ticker" required placeholder="AAPL" />
        </label>
        <label>
          Sources
          <select v-model="sourceGroup">
            <option value="all">all</option>
            <option value="yfinance">yfinance</option>
            <option value="rss">rss</option>
            <option value="reddit">reddit</option>
          </select>
        </label>
        <SubmitButton :busy="busy" busy-label="Fetching headlines…">Analyze</SubmitButton>
      </fieldset>
    </form>
    <div class="result">
      <ErrorBox v-if="error" :error="error" />
      <template v-if="result">
        <div class="stat-tile-row">
          <div class="stat-tile">
            <div class="stat-tile-label">Overall sentiment</div>
            <div :class="`stat-tile-value ${result.overall_sentiment != null ? directionClass(result.overall_sentiment) : ''}`">
              {{ result.overall_sentiment != null ? fmtSentiment(result.overall_sentiment) : 'n/a' }}
            </div>
          </div>
          <div class="stat-tile">
            <div class="stat-tile-label">Headlines</div>
            <div class="stat-tile-value">{{ result.item_count }}</div>
          </div>
          <div class="stat-tile">
            <div class="stat-tile-label">Sources</div>
            <div class="stat-tile-value">{{ result.source_group }}</div>
          </div>
        </div>

        <p v-if="result.item_count === 0" class="hint">No headlines found for this ticker/source combination.</p>

        <div v-if="result.daily.length > 0" class="table-scroll">
          <table class="data-table">
            <thead>
              <tr><th>Date</th><th>Mean</th><th>Count</th><th>% positive</th><th>% negative</th></tr>
            </thead>
            <tbody>
              <tr v-for="d in result.daily" :key="d.date">
                <td>{{ d.date }}</td>
                <td :class="directionClass(d.sentiment_mean)">{{ fmtSentiment(d.sentiment_mean) }}</td>
                <td>{{ d.sentiment_count }}</td>
                <td>{{ (d.pct_positive * 100).toFixed(0) }}%</td>
                <td>{{ (d.pct_negative * 100).toFixed(0) }}%</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="result.items.length > 0" class="table-scroll">
          <table class="data-table">
            <thead>
              <tr><th>Published</th><th>Source</th><th>Score</th><th>Title</th></tr>
            </thead>
            <tbody>
              <tr v-for="(item, i) in result.items" :key="i">
                <td>{{ new Date(item.published).toLocaleString() }}</td>
                <td>{{ item.source }}</td>
                <td :class="directionClass(item.score)">{{ fmtSentiment(item.score) }}</td>
                <td>{{ item.title }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </div>
  </section>
</template>
