"use client";

import { useState } from 'react';

type ImageInfo = {
  filename: string;
  url: string;
  clickable_link_found: boolean;
  size?: number;
};

type PageInfo = {
  page: number;
  images: ImageInfo[];
};

type ResultViewerProps = {
  result: PageInfo[];
};

export default function ResultViewer({ result }: ResultViewerProps) {
  const [loadedImages, setLoadedImages] = useState<Set<string>>(new Set());
  const [failedImages, setFailedImages] = useState<Set<string>>(new Set());

  const downloadReport = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(result, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", "report.json");
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  };

  const handleImageLoad = (url: string) => {
    setLoadedImages(prev => new Set(prev).add(url));
    setFailedImages(prev => {
      const newSet = new Set(prev);
      newSet.delete(url);
      return newSet;
    });
  };

  const handleImageError = (url: string) => {
    setFailedImages(prev => new Set(prev).add(url));
    setLoadedImages(prev => {
      const newSet = new Set(prev);
      newSet.delete(url);
      return newSet;
    });
  };

  const openImageInNewTab = (url: string) => {
    window.open(url, '_blank');
  };

  const filteredResult = result.map(page => ({
    ...page,
    images: page.images.filter(img => img.clickable_link_found)
  }));

  const totalClickableImages = filteredResult.reduce((acc, page) => acc + page.images.length, 0);
  const totalAllImages = result.reduce((acc, page) => acc + page.images.length, 0);

  return (
    <div className="p-8 space-y-8 bg-white">
      <div className="flex justify-between items-center border-b-2 border-gray-200 pb-6">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Extraction Results</h2>
          <p className="text-gray-600 mt-2">Analysis of embedded images in your PDF</p>
        </div>
        <button onClick={downloadReport} className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300">
          📥 Download Report
        </button>
      </div>

      {totalClickableImages === 0 ? (
        <div className="bg-yellow-50 border-2 border-yellow-200 rounded-2xl p-8 text-center">
          <div className="text-5xl mb-4">🔍</div>
          <h3 className="text-2xl font-bold text-yellow-800 mb-4">No Clickable Images Found</h3>
          <p className="text-yellow-700">The scanner analyzed {totalAllImages} images across {result.length} pages.</p>
        </div>
      ) : (
        <div className="space-y-6 max-h-[800px] overflow-y-auto pr-4">
          {filteredResult.map((page, idx) => (
            page.images.length > 0 && (
              <div key={idx} className="bg-white rounded-xl p-6 border border-red-300">
                <h4 className="text-xl font-semibold mb-4">Page {page.page} - {page.images.length} clickable image(s)</h4>
                <div className="flex space-x-4 overflow-x-auto">
                  {page.images.map((img, i) => (
                    <div key={i} className="border p-2 rounded-lg min-w-[200px] flex flex-col items-center">
                      <div className="w-full h-48 flex items-center justify-center bg-gray-100 mb-2">
                        <img 
                          src={img.url} 
                          alt={img.filename} 
                          onLoad={() => handleImageLoad(img.url)}
                          onError={() => handleImageError(img.url)}
                          className="max-h-full max-w-full object-contain cursor-pointer"
                          onClick={() => openImageInNewTab(img.url)}
                        />
                      </div>
                      <div className="text-sm text-gray-700 break-all text-center">{img.filename}</div>
                      <div className="text-xs text-red-600 font-bold mt-1">{img.clickable_link_found ? '⚠️ Clickable Link' : 'No Link'}</div>
                      <button onClick={() => openImageInNewTab(img.url)} className="mt-2 bg-blue-500 text-white px-2 py-1 rounded text-xs">View Image</button>
                    </div>
                  ))}
                </div>
              </div>
            )
          ))}
        </div>
      )}
    </div>
  );
}
