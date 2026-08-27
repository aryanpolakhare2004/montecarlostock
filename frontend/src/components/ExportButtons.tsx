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
  const [busy, setBusy] = useState<'png' | 'pdf' | null>(null);
  const { showToast } = useToast();

  function onCsv() {
    try {
      downloadBlob(csvFilename, toCsv(csvRows), 'text/csv');
    } catch (err) {
      showToast(`CSV export failed: ${err instanceof Error ? err.message : String(err)}`, 'error');
    }
  }

  async function onDownload(kind: 'png' | 'pdf') {
    setBusy(kind);
    try {
      const resp = await fetch(`/api/runs/${runId}/${kind}`);
      if (!resp.ok) throw new Error(`request failed (${resp.status})`);
      const blob = await resp.blob();
      downloadBlob(`run-${runId}.${kind}`, blob, kind === 'png' ? 'image/png' : 'application/pdf');
    } catch (err) {
      showToast(`${kind.toUpperCase()} export failed: ${err instanceof Error ? err.message : String(err)}`, 'error');
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="export-buttons">
      <button type="button" onClick={onCsv} disabled={csvRows.length === 0}>
        <DownloadIcon size={14} /> CSV
      </button>
      <button type="button" onClick={() => onDownload('png')} disabled={busy !== null}>
        <DownloadIcon size={14} /> PNG
      </button>
      <button type="button" onClick={() => onDownload('pdf')} disabled={busy !== null}>
        <DownloadIcon size={14} /> PDF
      </button>
    </div>
  );
}
