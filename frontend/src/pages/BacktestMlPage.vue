<script setup lang="ts">
import { ref } from 'vue';
import { api, ApiError } from '../api';
import StatTable from '../components/StatTable.vue';
import ErrorBox from '../components/ErrorBox.vue';
import ExportButtons from '../components/ExportButtons.vue';
import SubmitButton from '../components/SubmitButton.vue';
import FanChart from '../components/charts/FanChart.vue';
import type { useModels } from '../composables/useModels';
import type { BacktestMlResponse } from '../types';

type ModelOptions = ReturnType<typeof useModels>;
defineProps<{ modelOptions: ModelOptions }>();

const modelId = ref('');
const days = ref(60);
const sims = ref(10000);
const blockSize = ref(5);
const seed = ref('');
const busy = ref(false);
const result = ref<BacktestMlResponse | null>(null);
const error = ref<Error | null>(null);

async function onSubmit() {
  if (!modelId.value) {
    error.value = new Error('choose a trained model first');
    return;
  }
  busy.value = true;
  error.value = null;
  result.value = null;
  try {
    result.value = await api.backtestMl({
      model_id: Number(modelId.value), days: days.value, sims: sims.value, block_size: blockSize.value,
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
    <h2>Monte Carlo project a trained model's robustness</h2>
    <form class="run-form" @submit.prevent="onSubmit">
      <fieldset :disabled="busy" class="run-form-fields">
        <label>
          Model
          <select v-model="modelId">
            <option value="">(load models first)</option>
            <option v-for="m in modelOptions.models" :key="m.id" :value="String(m.id)">
              #{{ m.id }} {{ m.ticker }} {{ m.model_type }} (test acc {{ m.test_accuracy.toFixed(2) }})
            </option>
          </select>
        </label>
        <details class="advanced-fields">
          <summary>Advanced options</summary>
          <div class="advanced-fields-grid">
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
        <ExportButtons :run-id="result.run_id" :csv-filename="`backtest_ml_${result.run_id}.csv`" :csv-rows="result.bands" />
        <FanChart :data="result.bands" y-label="Equity (starting at 1.0)" />
      </template>
    </div>
  </section>
</template>
