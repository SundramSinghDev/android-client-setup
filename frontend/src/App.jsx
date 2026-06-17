import { useState } from 'react'
import ClientForm from './components/ClientForm'
import StatusPanel from './components/StatusPanel'

export default function App() {
  const [status, setStatus] = useState(null)

  return (
    <div style={{ maxWidth: 600, margin: '40px auto', padding: '0 16px', fontFamily: 'sans-serif' }}>
      <h1 style={{ marginBottom: 24 }}>New Client Project Setup</h1>
      <ClientForm onStatusChange={setStatus} />
      <StatusPanel status={status} />
    </div>
  )
}
