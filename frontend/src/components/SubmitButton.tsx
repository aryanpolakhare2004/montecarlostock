import type { ReactNode } from 'react';
import { Spinner } from './Spinner';

interface Props {
  busy: boolean;
  busyLabel?: string;
  children: ReactNode;
}

export function SubmitButton({ busy, busyLabel = 'Running…', children }: Props) {
  return (
    <button type="submit" disabled={busy} className="submit-btn">
      {busy ? (
        <>
          <Spinner size={14} /> {busyLabel}
        </>
      ) : (
        children
      )}
    </button>
  );
}
