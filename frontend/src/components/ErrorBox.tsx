interface Props {
  error: unknown;
}

export function ErrorBox({ error }: Props) {
  const message = error instanceof Error ? error.message : String(error);
  return <p className="error">{message}</p>;
}
