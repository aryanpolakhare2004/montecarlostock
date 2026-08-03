import { useCallback, useEffect, useState } from 'react';
import { api } from '../api';
import type { ModelRecord } from '../types';

export function useModels() {
  const [models, setModels] = useState<ModelRecord[]>([]);

  const reload = useCallback(() => {
    api.listModels().then(setModels).catch(() => setModels([]));
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  const technicalOnly = models.filter((m) => !m.sentiment_sources && !m.use_volume);

  return { models, technicalOnly, reload };
}
