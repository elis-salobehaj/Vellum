import { FileText, X } from 'lucide-react';
import type { Citation } from '../../types';

interface SourcePanelProps {
  source: Citation | null;
  onClose: () => void;
}

const SourcePanel = ({ source, onClose }: SourcePanelProps) => {
  if (!source) return null;

  return (
    <div className="w-96 border-l border-gray-200 bg-white h-full flex flex-col shadow-xl absolute right-0 top-0 z-10 lg:relative lg:shadow-none lg:z-0">
      <div className="p-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
        <div className="flex items-center gap-2 overflow-hidden">
          <FileText size={16} className="text-gray-500" />
          <span className="text-sm font-medium text-gray-700 truncate">{source.source}</span>
        </div>
        <button onClick={onClose} className="p-1 hover:bg-gray-200 rounded">
          <X size={16} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="bg-yellow-50 border border-yellow-100 p-4 rounded-lg mb-4 text-sm text-yellow-800">
          Found via vector search on Page {source.page}
        </div>

        <div className="mb-6">
          <a
            href={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/files/${source.source}`}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center text-blue-600 hover:underline text-sm"
          >
            <FileText size={14} className="mr-1" />
            Open original PDF
          </a>
        </div>

        <div className="prose prose-sm max-w-none text-gray-600 font-serif leading-relaxed">
          {source.text}
          <p className="mt-4 italic text-gray-400">[... context continues ...]</p>
        </div>
      </div>
    </div>
  );
};

export default SourcePanel;
