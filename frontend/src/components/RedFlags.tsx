import { AlertTriangle, ExternalLink } from 'lucide-react'
import type { RedFlag } from '../types'

interface Props {
  flags: RedFlag[]
  onPageClick: (page: number) => void
}

const SEVERITY_STYLES = {
  CRITICAL: 'bg-red-100 border-red-300 text-red-800',
  HIGH: 'bg-orange-100 border-orange-300 text-orange-800',
  MEDIUM: 'bg-yellow-100 border-yellow-300 text-yellow-800',
  LOW: 'bg-blue-100 border-blue-300 text-blue-800',
}

const SEVERITY_BADGES = {
  CRITICAL: 'bg-red-500 text-white',
  HIGH: 'bg-orange-500 text-white',
  MEDIUM: 'bg-yellow-500 text-black',
  LOW: 'bg-blue-500 text-white',
}

export function RedFlagsPanel({ flags, onPageClick }: Props) {
  if (flags.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-yellow-600" />
          Red Flags
        </h3>
        <div className="text-center py-8 text-green-600">
          <span className="text-4xl">✓</span>
          <p className="mt-2 font-medium">No significant issues found</p>
        </div>
      </div>
    )
  }

  // Sort by severity
  const sorted = [...flags].sort((a, b) => {
    const order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
    return order.indexOf(a.severity) - order.indexOf(b.severity)
  })

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <AlertTriangle className="w-5 h-5 text-yellow-600" />
        Red Flags ({flags.length})
      </h3>
      <div className="space-y-3">
        {sorted.map((flag, i) => (
          <div
            key={i}
            className={`p-3 rounded-lg border ${SEVERITY_STYLES[flag.severity as keyof typeof SEVERITY_STYLES] || SEVERITY_STYLES.MEDIUM}`}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-xs px-2 py-0.5 rounded font-medium ${SEVERITY_BADGES[flag.severity as keyof typeof SEVERITY_BADGES] || SEVERITY_BADGES.MEDIUM}`}>
                    {flag.severity}
                  </span>
                  <span className="text-xs text-gray-500">{flag.category}</span>
                </div>
                <h4 className="font-semibold">{flag.title}</h4>
                <p className="text-sm mt-1">{flag.description}</p>
              </div>
            </div>
            <div className="flex items-center justify-between mt-2 pt-2 border-t border-current/20">
              <span className="text-xs">{flag.recommended_action}</span>
              {flag.pages_to_verify.length > 0 && (
                <div className="flex gap-1">
                  {flag.pages_to_verify.map(p => (
                    <button
                      key={p}
                      onClick={() => onPageClick(p)}
                      className="text-xs px-2 py-1 bg-white/50 rounded hover:bg-white/80 flex items-center gap-1"
                    >
                      p.{p}
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
