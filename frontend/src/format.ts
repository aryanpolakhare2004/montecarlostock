export function fmtScore(x: number | null | undefined): string {
  return x === null || x === undefined ? 'n/a' : x.toFixed(1);
}

export function fmtPct(x: number | null | undefined): string {
  return x === null || x === undefined ? 'n/a' : `${(x * 100).toFixed(1)}%`;
}

export function fmtMoney(x: number | null | undefined): string {
  return x === null || x === undefined
    ? 'n/a'
    : `$${x.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}
