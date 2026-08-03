import { useEffect, useRef, useState } from 'react';
import { api } from '../api';

interface Entry {
  command: string | null;
  output: string;
}

const WELCOME: Entry = {
  command: null,
  output:
    "mcstock terminal -- type 'help' for commands.\n" +
    "Try: analyst MSFT   |   compare MU,WDC,STX   |   price AAPL --days 60",
};

export function TerminalPage() {
  const [entries, setEntries] = useState<Entry[]>([WELCOME]);
  const [input, setInput] = useState('');
  const [history, setHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: 'end' });
  }, [entries]);

  async function runCommand(command: string) {
    const trimmed = command.trim();
    if (!trimmed) return;

    if (trimmed.toLowerCase() === 'clear') {
      setEntries([]);
      setInput('');
      setHistory((h) => [...h, trimmed]);
      setHistoryIndex(null);
      return;
    }

    setHistory((h) => [...h, trimmed]);
    setHistoryIndex(null);
    setInput('');
    setBusy(true);
    try {
      const response = await api.terminal({ command: trimmed });
      setEntries((e) => [...e, { command: trimmed, output: response.output }]);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setEntries((e) => [...e, { command: trimmed, output: `error: ${message}` }]);
    } finally {
      setBusy(false);
    }
  }

  function onKeyDown(evt: React.KeyboardEvent<HTMLInputElement>) {
    if (evt.key === 'Enter') {
      runCommand(input);
    } else if (evt.key === 'ArrowUp') {
      evt.preventDefault();
      if (history.length === 0) return;
      const nextIndex = historyIndex === null ? history.length - 1 : Math.max(0, historyIndex - 1);
      setHistoryIndex(nextIndex);
      setInput(history[nextIndex]);
    } else if (evt.key === 'ArrowDown') {
      evt.preventDefault();
      if (historyIndex === null) return;
      const nextIndex = historyIndex + 1;
      if (nextIndex >= history.length) {
        setHistoryIndex(null);
        setInput('');
      } else {
        setHistoryIndex(nextIndex);
        setInput(history[nextIndex]);
      }
    }
  }

  return (
    <section className="terminal-page" onClick={() => inputRef.current?.focus()}>
      <h2>Terminal</h2>
      <p className="hint">
        A text-only console over the same backend as the other tabs -- <code>help</code> lists every command.
        Output is plain text/ASCII, so it stays scriptable and fast to scan.
      </p>
      <div className="terminal">
        {entries.map((entry, i) => (
          <div className="terminal-entry" key={i}>
            {entry.command !== null && <div className="terminal-prompt-line">mcstock&gt; {entry.command}</div>}
            <pre className="terminal-output">{entry.output}</pre>
          </div>
        ))}
        {busy && <div className="terminal-output terminal-busy">running…</div>}
        <div className="terminal-input-line">
          <span className="terminal-prompt">mcstock&gt;</span>
          <input
            ref={inputRef}
            className="terminal-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            autoFocus
            spellCheck={false}
            autoComplete="off"
          />
        </div>
        <div ref={bottomRef} />
      </div>
    </section>
  );
}
