<script setup lang="ts">
import { ref } from 'vue';
import { api, runChartUrl } from '../api';
import ErrorBox from '../components/ErrorBox.vue';
import type { ModelRecord, RunRecord } from '../types';

function fmtWhen(iso: string): string {
  return iso.replace('T', ' ').slice(0, 19);
}

const runs = ref<RunRecord[] | null>(null);
const models = ref<ModelRecord[] | null>(null);
const runsError = ref<Error | null>(null);
const modelsError = ref<Error | null>(null);

function load() {
  runs.value = null;
  models.value = null;
  runsError.value = null;
  modelsError.value = null;
  api.listRuns().then((r) => { runs.value = r; }).catch((e) => { runsError.value = e; });
  api.listModels().then((r) => { models.value = r; }).catch((e) => { modelsError.value = e; });
}

load();
</script>

<template>
  <section>
    <h2>History</h2>
    <button class="refresh-btn" @click="load">Refresh</button>

    <h3>Simulation runs</h3>
    <ErrorBox v-if="runsError" :error="runsError" />
    <p v-else-if="runs === null">Loading…</p>
    <p v-else-if="runs.length === 0">No runs yet.</p>
    <div v-else class="table-scroll">
      <table class="data-table">
        <thead>
          <tr><th>ID</th><th>Type</th><th>Ticker</th><th>When</th><th>Chart</th></tr>
        </thead>
        <tbody>
          <tr v-for="r in runs" :key="r.id">
            <td>{{ r.id }}</td>
            <td>{{ r.run_type }}</td>
            <td>{{ r.ticker }}</td>
            <td>{{ fmtWhen(r.created_at) }}</td>
            <td><a v-if="r.has_chart" :href="runChartUrl(r.id)" target="_blank" rel="noreferrer">view</a></td>
          </tr>
        </tbody>
      </table>
    </div>

    <h3>Trained models</h3>
    <ErrorBox v-if="modelsError" :error="modelsError" />
    <p v-else-if="models === null">Loading…</p>
    <p v-else-if="models.length === 0">No trained models yet.</p>
    <div v-else class="table-scroll">
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th><th>Ticker</th><th>Model</th><th>Sentiment</th><th>Volume</th>
            <th>Train acc</th><th>Test acc</th><th>When</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in models" :key="m.id">
            <td>{{ m.id }}</td>
            <td>{{ m.ticker }}</td>
            <td>{{ m.model_type }}</td>
            <td>{{ m.sentiment_sources ? m.sentiment_sources.join(',') : 'none' }}</td>
            <td>{{ m.use_volume ? 'yes' : 'no' }}</td>
            <td>{{ m.train_accuracy.toFixed(3) }}</td>
            <td>{{ m.test_accuracy.toFixed(3) }}</td>
            <td>{{ fmtWhen(m.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
