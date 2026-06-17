export default function StatusPanel({ status }) {
  if (!status) return null
  const { state, message, repoUrl } = status
  return (
    <div className={`status-panel ${state}`}>
      <p className="status-message">{message}</p>
      {repoUrl && (
        <p className="status-link">
          Repo: <a href={repoUrl} target="_blank" rel="noreferrer">{repoUrl}</a>
        </p>
      )}
    </div>
  )
}
