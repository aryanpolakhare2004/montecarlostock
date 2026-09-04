<script setup lang="ts">
import { ref } from 'vue';
import { api, ApiError } from '../api';
import ErrorBox from '../components/ErrorBox.vue';
import ScoreCard from '../components/ScoreCard.vue';
import SubmitButton from '../components/SubmitButton.vue';
import type { FundamentalsReport } from '../types';

const ticker = ref('MSFT');
const llmBackend = ref('');
const forceRefresh = ref(false);
const busy = ref(false);
const result = ref<FundamentalsReport | null>(null);
const error = ref<Error | null>(null);

async function onSubmit() {
  busy.value = true;
  error.value = null;
  result.value = null;
  try {
    result.value = await api.fundamentals({
      ticker: ticker.value,
      llm_backend: llmBackend.value || null,
      force_refresh: forceRefresh.value,
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
    <h2>AI investment analyst</h2>
    <p class="hint">
      Pulls structured financials straight from SEC EDGAR, engineers ratios, and scores the business numerically.
      Bull/bear case and red flags are rendered from that same evidence &mdash; by a local template unless a local
      LLM backend (e.g. Ollama) is configured.
    </p>
    <form class="run-form" @submit.prevent="onSubmit">
      <fieldset :disabled="busy" class="run-form-fields">
        <label>
          Ticker
          <input v-model="ticker" required placeholder="MSFT" />
        </label>
        <label>
          LLM backend
          <select v-model="llmBackend">
            <option value="">(server default)</option>
            <option value="stub">stub (no LLM)</option>
            <option value="ollama">ollama</option>
            <option value="together">together</option>
          </select>
        </label>
        <label class="checkbox">
          <input type="checkbox" v-model="forceRefresh" />
          Force refresh from SEC
        </label>
        <SubmitButton :busy="busy" busy-label="Fetching filings…">Analyze</SubmitButton>
      </fieldset>
    </form>
    <div class="result">
      <ErrorBox v-if="error" :error="error" />
      <ScoreCard v-if="result" :report="result" />
    </div>
  </section>
</template>
