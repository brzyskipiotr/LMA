import { useState } from 'react'
import { Upload, FileText, Loader2 } from 'lucide-react'
import type { AnalysisReport } from './types'
import { ScoreCardPanel } from './components/ScoreCard'
import { FactsTable } from './components/FactsTable'
import { RedFlagsPanel } from './components/RedFlags'
import { PVGISPanel } from './components/PVGISPanel'
import { PageViewer } from './components/PageViewer'
import { API_BASE } from './config'

export default function App() {
  const [report, setReport] = useState<AnalysisReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedPage, setSelectedPage] = useState<number | null>(null)

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setLoading(true)
    setError(null)
    setReport(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        throw new Error(await res.text())
      }

      const data = await res.json()
      setReport(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100">
      {/* Header */}
      <header className="bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center gap-3">
          <div className="w-10 h-10 bg-green-600 rounded-lg flex items-center justify-center">
            <FileText className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">GreenLoan Validator</h1>
            <p className="text-sm text-gray-500">PV Document Analysis for Green Loan Origination</p>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Upload */}
        {!report && !loading && (
          <div className="bg-white rounded-xl shadow-lg p-8 max-w-xl mx-auto">
            <label className="flex flex-col items-center justify-center w-full h-64 border-2 border-dashed border-green-300 rounded-xl cursor-pointer hover:bg-green-50 transition-colors">
              <Upload className="w-12 h-12 text-green-500 mb-4" />
              <span className="text-lg font-medium text-gray-700">Drop PDF or click to upload</span>
              <span className="text-sm text-gray-500 mt-2">PV installation docs, offers, applications</span>
              <input type="file" accept=".pdf" className="hidden" onChange={handleUpload} />
            </label>
            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                {error}
              </div>
            )}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="bg-white rounded-xl shadow-lg p-12 max-w-xl mx-auto text-center">
            <Loader2 className="w-12 h-12 text-green-500 animate-spin mx-auto mb-4" />
            <p className="text-lg font-medium text-gray-700">Analyzing document...</p>
            <p className="text-sm text-gray-500 mt-2">Text extraction, OCR, data verification</p>
          </div>
        )}

        {/* Results */}
        {report && (
          <div className="space-y-6">
            {/* Document info */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <FileText className="w-10 h-10 text-green-600" />
                  <div>
                    <h2 className="text-lg font-semibold">{report.document.filename}</h2>
                    <p className="text-sm text-gray-500">
                      {report.document.pages} pages • {report.document.doc_id}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setReport(null)
                    setSelectedPage(null)
                  }}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium transition-colors"
                >
                  New Analysis
                </button>
              </div>
            </div>

            {/* Scorecard */}
            <ScoreCardPanel scorecard={report.scorecard} />

            {/* PVGIS Panel */}
            <PVGISPanel verifications={report.verifications} onPageClick={setSelectedPage} />

            {/* Main content grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Facts */}
              <FactsTable facts={report.facts} onPageClick={setSelectedPage} />

              {/* Red Flags */}
              <RedFlagsPanel flags={report.red_flags} onPageClick={setSelectedPage} />
            </div>

            {/* Page Viewer */}
            {selectedPage && (
              <PageViewer
                docId={report.document.doc_id}
                pageNo={selectedPage}
                totalPages={report.document.pages}
                onClose={() => setSelectedPage(null)}
                onNavigate={setSelectedPage}
              />
            )}
          </div>
        )}
      </main>
    </div>
  )
}
