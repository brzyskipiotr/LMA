import { CheckCircle, AlertTriangle, XCircle } from 'lucide-react'
import type { ScoreCard } from '../types'

interface Props {
  scorecard: ScoreCard
}

export function ScoreCardPanel({ scorecard }: Props) {
  const lightColors = {
    GREEN: 'bg-green-500',
    YELLOW: 'bg-yellow-500',
    RED: 'bg-red-500',
  }

  const lightIcons = {
    GREEN: CheckCircle,
    YELLOW: AlertTriangle,
    RED: XCircle,
  }

  const LightIcon = lightIcons[scorecard.traffic_light as keyof typeof lightIcons] || AlertTriangle

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <div className="flex items-center gap-6">
        {/* Traffic light */}
        <div className={`w-20 h-20 rounded-full ${lightColors[scorecard.traffic_light as keyof typeof lightColors]} flex items-center justify-center shadow-lg`}>
          <LightIcon className="w-10 h-10 text-white" />
        </div>

        {/* Scores */}
        <div className="flex-1 grid grid-cols-3 gap-4">
          <ScoreBar label="Evidence Coverage" value={scorecard.evidence_coverage} />
          <ScoreBar label="Consistency" value={scorecard.consistency} />
          <ScoreBar label="Feasibility" value={scorecard.feasibility} />
        </div>
      </div>

      {/* Missing data */}
      {scorecard.missing_data.length > 0 && (
        <div className="mt-4 pt-4 border-t">
          <p className="text-sm text-gray-500">
            <span className="font-medium">Missing data: </span>
            {scorecard.missing_data.map(f => f.replace(/_/g, ' ')).join(', ')}
          </p>
        </div>
      )}

      {/* Pages to verify */}
      {scorecard.pages_to_verify.length > 0 && (
        <div className="mt-2">
          <p className="text-sm text-gray-500">
            <span className="font-medium">Pages to verify: </span>
            {scorecard.pages_to_verify.join(', ')}
          </p>
        </div>
      )}
    </div>
  )
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const color = value >= 70 ? 'bg-green-500' : value >= 45 ? 'bg-yellow-500' : 'bg-red-500'

  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-600">{label}</span>
        <span className="font-semibold">{value}%</span>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full ${color} transition-all`} style={{ width: `${value}%` }} />
      </div>
    </div>
  )
}
