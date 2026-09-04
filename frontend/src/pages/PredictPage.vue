<script setup lang="ts">
import { ref } from 'vue';
import { api, ApiError } from '../api';
import ErrorBox from '../components/ErrorBox.vue';
import SubmitButton from '../components/SubmitButton.vue';
import type { useModels } from '../composables/useModels';
import type { PredictResponse } from '../types';

type ModelOptions = ReturnType<typeof useModels>;
defineProps<{ modelOptions: ModelOptions }>();

const modelId = ref('');
const busy = ref(false);
const result = ref<PredictResponse | null>(null);
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
    result.value = await api.predict({ model_id: Number(modelId.value) });
  } catch (err) {
    error.value = err instanceof ApiError ? err : new Error(String(err));
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <section>
    <h2>Predict next-period direction</h2>
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
        <SubmitButton :busy="busy" busy-label="Predicting…">Predict</SubmitButton>
      </fieldset>
    </form>
    <div class="result">
      <ErrorBox v-if="error" :error="error" />
      <p v-if="result">
        {{ result.ticker }}:
        <span :class="`direction ${result.direction === 'UP' ? 'up' : 'down'}`">{{ result.direction }}</span>
        next {{ result.horizon }}-day move &mdash; P(up)={{ result.prob_up.toFixed(3) }}
      </p>
    </div>
  </section>
</template>
