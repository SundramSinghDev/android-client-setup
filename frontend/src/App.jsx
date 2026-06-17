import { useState } from 'react'
import ClientForm from './components/ClientForm'
import StatusPanel from './components/StatusPanel'
import './App.css'

export default function App() {
  const [status, setStatus] = useState(null)

  return (
    <div className="page">
      <h1 className="page-title">New Client Project Setup</h1>
      <div className="card">
        <ClientForm onStatusChange={setStatus} />
      </div>
      <StatusPanel status={status} />
    </div>
  )
}
