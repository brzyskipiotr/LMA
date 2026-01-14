import { Sun, MapPin, ExternalLink, AlertTriangle, CheckCircle } from 'lucide-react'
import type { VerificationResult } from '../types'

interface Props {
  verifications: VerificationResult[]
  onPageClick: (page: number) => void
}

export function PVGISPanel({ verifications, onPageClick }: Props) {
  const pvgisCheck = verifications.find(v => v.check_type === "PVGIS_YIELD_SANITY")

  if (!pvgisCheck) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Sun className="w-5 h-5 text-yellow-500" />
          PVGIS Yield Check
        </h3>
        <div className="text-center py-6 text-gray-500">
          <p className="text-sm">PVGIS check not available</p>
          <p className="text-xs mt-2">Missing: location, power, or yield data</p>
        </div>
      </div>
    )
  }

  const { inputs, outputs, delta_pct, severity, why, pages_to_verify } = pvgisCheck
  const declaredYield = inputs.declared_kwh_per_kwp as number
  const pvgisYield = outputs.pvgis_kwh_per_kwp_estimate as number
  const location = inputs.location as string
  const lat = inputs.lat as number
  const lon = inputs.lon as number
  const source = inputs.declared_source as string

  const severityColors = {
    OK: 'bg-green-100 text-green-800 border-green-200',
    MEDIUM: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    HIGH: 'bg-red-100 text-red-800 border-red-200',
  }

  const severityIcons = {
    OK: <CheckCircle className="w-5 h-5 text-green-600" />,
    MEDIUM: <AlertTriangle className="w-5 h-5 text-yellow-600" />,
    HIGH: <AlertTriangle className="w-5 h-5 text-red-600" />,
  }

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Sun className="w-5 h-5 text-yellow-500" />
        PVGIS Yield Check
      </h3>

      {/* Location */}
      <div className="flex items-start gap-2 mb-4 text-sm text-gray-600">
        <MapPin className="w-4 h-4 mt-0.5 flex-shrink-0" />
        <div>
          <p className="font-medium">{location}</p>
          <p className="text-xs text-gray-400">
            {lat.toFixed(4)}°N, {lon.toFixed(4)}°E
          </p>
        </div>
      </div>

      {/* Comparison */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-500 mb-1">Declared Yield</p>
          <p className="text-xl font-bold text-gray-900">{declaredYield?.toFixed(0)}</p>
          <p className="text-xs text-gray-500">kWh/kWp/year</p>
          {source === "IMPLIED_FROM_ANNUAL" && (
            <p className="text-xs text-blue-500 mt-1">*Implied from annual energy</p>
          )}
        </div>
        <div className="bg-blue-50 rounded-lg p-3">
          <p className="text-xs text-gray-500 mb-1">PVGIS Estimate</p>
          <p className="text-xl font-bold text-blue-700">{pvgisYield?.toFixed(0)}</p>
          <p className="text-xs text-gray-500">kWh/kWp/year</p>
        </div>
      </div>

      {/* Delta */}
      <div className={`rounded-lg p-4 border ${severityColors[severity as keyof typeof severityColors] || severityColors.OK}`}>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            {severityIcons[severity as keyof typeof severityIcons] || severityIcons.OK}
            <span className="font-semibold">
              {delta_pct !== null && delta_pct > 0 ? '+' : ''}{delta_pct?.toFixed(1)}% Delta
            </span>
          </div>
          <span className={`text-xs px-2 py-1 rounded font-medium ${
            severity === 'OK' ? 'bg-green-200' :
            severity === 'MEDIUM' ? 'bg-yellow-200' :
            'bg-red-200'
          }`}>
            {severity}
          </span>
        </div>
        <p className="text-sm">{why}</p>
      </div>

      {/* Pages to verify */}
      {pages_to_verify.length > 0 && (
        <div className="mt-4 pt-4 border-t">
          <p className="text-xs text-gray-500 mb-2">Evidence pages:</p>
          <div className="flex gap-2 flex-wrap">
            {pages_to_verify.map(p => (
              <button
                key={p}
                onClick={() => onPageClick(p)}
                className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 flex items-center gap-1"
              >
                p.{p}
                <ExternalLink className="w-3 h-3" />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* PVGIS attribution */}
      <p className="text-xs text-gray-400 mt-4">
        Data source: EU JRC PVGIS 5.2
      </p>
    </div>
  )
}
