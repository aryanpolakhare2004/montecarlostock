<script setup lang="ts">
import { ref } from 'vue';
import { api, ApiError } from '../api';
import ErrorBox from '../components/ErrorBox.vue';
import SubmitButton from '../components/SubmitButton.vue';
import { useToast } from '../composables/useToast';
import type { TrainRequest, TrainResponse } from '../types';

const emit = defineEmits<{ trained: [] }>();

const ticker = ref('AAPL');
const model = ref<TrainRequest['model']>('logreg');
const sentiment = ref<TrainRequest['sentiment']>('none');
const useVolume = ref(true);
const period = ref('5y');
const horizon = ref(1);
const testSize = ref(0.2);
const busy = ref(false);
const result = ref<TrainResponse | null>(null);
const error = ref<Error | null>(null);
const { showToast } = useToast();

async function onSubmit() {
  busy.value = true;
  error.value = null;
  result.value = null;
  try {
    const response = await api.train({
      ticker: ticker.value, model: model.value, sentiment: sentiment.value, use_volume: useVolume.value,
      period: period.value, horizon: horizon.value, test_size: testSize.value,
    });
    result.value = response;
    emit('trained');
    showToast(`Trained model #${response.model_id} for ${ticker.value.toUpperCase()}`, 'success');
  } catch (err) {
    const errorObj = err instanceof ApiError ? err : new Error(String(err));
    error.value = errorObj;
    showToast(`Training failed: ${errorObj.message}`, 'error');
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <section>
    <h2>Train an ML classifier (binary up/down)</h2>
    <form class="run-form" @submit.prevent="onSubmit">
      <fieldset :disabled="busy" class="run-form-fields">
        <label>
          Ticker
          <input v-model="ticker" required placeholder="AAPL" />
        </label>
        <label>
          Model
          <select v-model="model">
            <option value="logreg">logreg</option>
            <option value="random_forest">random_forest</option>
            <option value="gradient_boosting">gradient_boosting</option>
          </select>
        </label>
        <label>
          Sentiment
          <select v-model="sentiment">
            <option value="none">none</option>
            <option value="yfinance">yfinance</option>
            <option value="rss">rss</option>
            <option value="reddit">reddit</option>
            <option value="all">all</option>
          </select>
        </label>
        <label class="checkbox">
          <input type="checkbox" v-model="useVolume" />
          Use volume features
        </label>
        <details class="advanced-fields">
          <summary>Advanced options</summary>
          <div class="advanced-fields-grid">
            <label>
              Period
              <input v-model="period" />
            </label>
            <label>
              Horizon (days ahead)
              <input type="number" min="1" v-model.number="horizon" />
            </label>
            <label>
              Test size
              <input type="number" min="0.05" max="0.5" step="0.05" v-model.number="testSize" />
            </label>
          </div>
        </details>
        <SubmitButton :busy="busy" busy-label="Training…">Train</SubmitButton>
      </fieldset>
    </form>
    <p class="hint">
      Tip: to later use a model with strategy <code>ml-technical</code>, train with sentiment
      <code>none</code> and volume features unchecked.
    </p>
    <div class="result">
      <p v-if="busy" class="hint">Training… this can take a while (fetching data/news, fitting the model).</p>
      <ErrorBox v-if="error" :error="error" />
      <template v-if="result">
        <p>
          Saved as model #{{ result.model_id }} &mdash; train_accuracy={{ result.train_accuracy.toFixed(4) }}, test_accuracy=
          {{ result.test_accuracy.toFixed(4) }}
        </p>
        <pre class="report">{{ result.test_report }}</pre>
      </template>
    </div>
  </section>
</template>
