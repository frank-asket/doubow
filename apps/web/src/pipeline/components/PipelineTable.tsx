import type { Application } from '@doubow/shared'

export function PipelineTable({ applications }: { applications: Application[] }) {
  return (
    <div className="card overflow-hidden">
      <table className="w-full text-sm">
        <tbody>
          {applications.map((application) => (
            <tr key={application.id} className="border-b border-surface-100">
              <td className="px-3 py-2">{application.job.company}</td>
              <td className="px-3 py-2">{application.job.title}</td>
              <td className="px-3 py-2">{application.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
