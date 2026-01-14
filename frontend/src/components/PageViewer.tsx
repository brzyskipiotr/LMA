import { X, ChevronLeft, ChevronRight } from 'lucide-react'
import { API_BASE } from '../config'

interface Props {
  docId: string
  pageNo: number
  totalPages: number
  onClose: () => void
  onNavigate: (page: number) => void
}

export function PageViewer({ docId, pageNo, totalPages, onClose, onNavigate }: Props) {
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-4">
            <button
              onClick={() => pageNo > 1 && onNavigate(pageNo - 1)}
              disabled={pageNo <= 1}
              className="p-2 hover:bg-gray-100 rounded disabled:opacity-30"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <span className="font-medium">
              Page {pageNo} of {totalPages}
            </span>
            <button
              onClick={() => pageNo < totalPages && onNavigate(pageNo + 1)}
              disabled={pageNo >= totalPages}
              className="p-2 hover:bg-gray-100 rounded disabled:opacity-30"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Image */}
        <div className="flex-1 overflow-auto p-4 bg-gray-100">
          <img
            src={`${API_BASE}/api/page/${docId}/${pageNo}`}
            alt={`Page ${pageNo}`}
            className="max-w-full mx-auto shadow-lg"
          />
        </div>
      </div>
    </div>
  )
}
