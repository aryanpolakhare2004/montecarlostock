interface Props {
  summary: object;
}

export function StatTable({ summary }: Props) {
  return (
    <table className="stat-table">
      <tbody>
        {Object.entries(summary as Record<string, unknown>).map(([key, value]) => (
          <tr key={key}>
            <td>{key}</td>
            <td>{typeof value === 'number' ? value.toFixed(4) : String(value)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
