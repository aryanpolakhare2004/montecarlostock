import { computed, reactive, ref } from 'vue';
import { api } from '../api';
import type { ModelRecord } from '../types';

export function useModels() {
  const models = ref<ModelRecord[]>([]);

  function reload() {
    api.listModels().then((r) => { models.value = r; }).catch(() => { models.value = []; });
  }

  reload();

  const technicalOnly = computed(() => models.value.filter((m) => !m.sentiment_sources && !m.use_volume));

  return reactive({ models, technicalOnly, reload });
}
