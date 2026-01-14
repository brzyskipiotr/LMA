import { FileText, ExternalLink } from 'lucide-react'
import type { ExtractedFact } from '../types'

interface Props {
  facts: ExtractedFact[]
  onPageClick: (page: number) => void
}

const FIELD_LABELS: Record<string, string> = {
  project_location_text: 'Location',
  declared_power_kwp: 'Installed Power',
  system_type: 'System Type',
  declared_yield_kwh_per_kwp: 'Expected Yield',
  declared_annual_energy_mwh: 'Annual Energy',
  capex_pln: 'CAPEX',
  roof_area_m2: 'Roof Area',
  panels_count: 'Panel Count',
  module_watt_peak: 'Module Power',
  inverter_power_kw: 'Inverter Power',
  grid_connection_status: 'Grid Connection',
  supplier_epc: 'EPC Contractor',
}

export function FactsTable({ facts, onPageClick }: Props) {
  if (facts.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5 text-green-600" />
          Extracted Facts
        </h3>
        <p className="text-gray-500 text-center py-8">No PV facts found in document</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <FileText className="w-5 h-5 text-green-600" />
        Extracted Facts ({facts.length})
      </h3>
      <div className="space-y-3">
        {facts.map((fact, i) => (
          <div key={i} className="p-3 bg-gray-50 rounded-lg">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <span className="text-sm text-gray-500">
                  {FIELD_LABELS[fact.field] || fact.field}
                </span>
                <div className="font-semibold text-gray-900">
                  {fact.value ?? '—'}
                  {fact.unit && <span className="text-gray-500 ml-1">{fact.unit}</span>}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-xs px-2 py-1 rounded ${
                  fact.confidence >= 0.8 ? 'bg-green-100 text-green-700' :
                  fact.confidence >= 0.6 ? 'bg-yellow-100 text-yellow-700' :
                  'bg-red-100 text-red-700'
                }`}>
                  {Math.round(fact.confidence * 100)}%
                </span>
                {fact.evidence.map((e, j) => (
                  <button
                    key={j}
                    onClick={() => onPageClick(e.page_no)}
                    className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 flex items-center gap-1"
                  >
                    p.{e.page_no}
                    <ExternalLink className="w-3 h-3" />
                  </button>
                ))}
              </div>
            </div>
            {fact.evidence[0]?.snippet && (
              <p className="text-xs text-gray-500 mt-2 italic border-l-2 border-gray-300 pl-2">
                "{fact.evidence[0].snippet}"
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
