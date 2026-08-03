interface Props {
  base64Png: string | null | undefined;
}

export function ChartImage({ base64Png }: Props) {
  if (!base64Png) return null;
  return <img alt="chart" src={`data:image/png;base64,${base64Png}`} />;
}
