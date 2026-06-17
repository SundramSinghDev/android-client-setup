export default function StatusPanel({ status }) {
  if (!status) return null

  const { state, message, repoUrl } = status

  const colors = { idle: '#888', loading: '#f0a500', success: '#2e7d32', error: '#c62828' }
  const color = colors[state] || '#888'

  return (
    <div style={{ marginTop: 24, padding: 16, border: `2px solid ${color}`, borderRadius: 8 }}>
      <p style={{ color, fontWeight: 600, margin: 0 }}>{message}</p>
      {repoUrl && (
        <p style={{ marginTop: 8 }}>
          Repo: <a href={repoUrl} target="_blank" rel="noreferrer">{repoUrl}</a>
        </p>
      )}
    </div>
  )
}
