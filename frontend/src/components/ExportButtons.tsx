import { useState } from 'react';
import { DownloadIcon } from './icons';
import { useToast } from './toast';
import { downloadBlob, toCsv } from '../utils/csv';

interface ExportButtonsProps<T extends object> {
  runId: number;
  csvFilename: string;
  csvRows: T[];
}

export function ExportButtons<T extends object>({ runId, csvFilename, csvRows }: ExportButtonsProps<T>) {
  const [busy, setBusy] = useState(false);
  const { showToast } = useToast();

  function onCsv() {
    try {
      downloadBlob(csvFilename, toCsv(csvRows), 'text/csv');
    } catch (err) {
      showToast(`CSV export failed: ${err instanceof Error ? err.message : String(err)}`, 'error');
    }
  }

  async function onPng() {
    setBusy(true);
    try {
      const resp = await fetch(`/api/runs/${runId}/chart`);
      if (!resp.ok) throw new Error(`request failed (${resp.status})`);
      const blob = await resp.blob();
      downloadBlob(`run-${runId}.png`, blob, 'image/png');
    } catch (err) {
      showToast(`PNG export failed: ${err instanceof Error ? err.message : String(err)}`, 'error');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="export-buttons">
      <button type="button" onClick={onCsv} disabled={csvRows.length === 0}>
        <DownloadIcon size={14} /> CSV
      </button>
      <button type="button" onClick={onPng} disabled={busy}>
        <DownloadIcon size={14} /> PNG
      </button>
    </div>
  );
}
