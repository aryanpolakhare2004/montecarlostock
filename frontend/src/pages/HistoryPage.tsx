import { useCallback, useEffect, useState } from 'react';
import { api, runChartUrl } from '../api';
import { ErrorBox } from '../components/ErrorBox';
import type { ModelRecord, RunRecord } from '../types';

function fmtWhen(iso: string): string {
  return iso.replace('T', ' ').slice(0, 19);
}

export function HistoryPage() {
  const [runs, setRuns] = useState<RunRecord[] | null>(null);
  const [models, setModels] = useState<ModelRecord[] | null>(null);
  const [runsError, setRunsError] = useState<Error | null>(null);
  const [modelsError, setModelsError] = useState<Error | null>(null);

  const load = useCallback(() => {
    setRuns(null);
    setModels(null);
    setRunsError(null);
    setModelsError(null);
    api.listRuns().then(setRuns).catch(setRunsError);
    api.listModels().then(setModels).catch(setModelsError);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <section>
      <h2>History</h2>
      <button className="refresh-btn" onClick={load}>Refresh</button>

      <h3>Simulation runs</h3>
      {runsError && <ErrorBox error={runsError} />}
      {!runsError && runs === null && <p>Loading…</p>}
      {!runsError && runs && runs.length === 0 && <p>No runs yet.</p>}
      {!runsError && runs && runs.length > 0 && (
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr><th>ID</th><th>Type</th><th>Ticker</th><th>When</th><th>Chart</th></tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.id}>
                  <td>{r.id}</td>
                  <td>{r.run_type}</td>
                  <td>{r.ticker}</td>
                  <td>{fmtWhen(r.created_at)}</td>
                  <td>{r.has_chart ? <a href={runChartUrl(r.id)} target="_blank" rel="noreferrer">view</a> : ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <h3>Trained models</h3>
      {modelsError && <ErrorBox error={modelsError} />}
      {!modelsError && models === null && <p>Loading…</p>}
      {!modelsError && models && models.length === 0 && <p>No trained models yet.</p>}
      {!modelsError && models && models.length > 0 && (
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th><th>Ticker</th><th>Model</th><th>Sentiment</th><th>Volume</th>
                <th>Train acc</th><th>Test acc</th><th>When</th>
              </tr>
            </thead>
            <tbody>
              {models.map((m) => (
                <tr key={m.id}>
                  <td>{m.id}</td>
                  <td>{m.ticker}</td>
                  <td>{m.model_type}</td>
                  <td>{m.sentiment_sources ? m.sentiment_sources.join(',') : 'none'}</td>
                  <td>{m.use_volume ? 'yes' : 'no'}</td>
                  <td>{m.train_accuracy.toFixed(3)}</td>
                  <td>{m.test_accuracy.toFixed(3)}</td>
                  <td>{fmtWhen(m.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
