"use client";

import { useState } from "react";
import Image from "next/image";

type LinkInfo = {
  type: string;
  content: string;
  description?: string;
  confidence?: number;
  bbox?: number[]; // NEW: For PDF structural links
};

type ImageInfo = {
  filename: string;
  url: string;
  clickable_links_found: boolean;
  extracted_links?: LinkInfo[];
  size?: number;
  image_area?: number[]; // NEW: Image coordinates
};

type PageInfo = {
  page: number;
  images: ImageInfo[];
};

type ResultViewerProps = {
  result: PageInfo[];
};

export default function ResultViewer({ result }: ResultViewerProps) {
  const [failedImages, setFailedImages] = useState<Set<string>>(new Set());

  const downloadReport = () => {
    const dataStr =
      "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(result, null, 2));
    const downloadAnchorNode = document.createElement("a");
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", "report.json");
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  };

  const handleImageError = (url: string) => {
    setFailedImages((prev) => new Set(prev).add(url));
  };

  const openLink = (url: string) => {
    window.open(url, "_blank");
  };

  // NEW: Improved link type detection with better labels
  const getLinkLabel = (linkType: string) => {
    const typeMap: { [key: string]: string } = {
      'pdf_structural': '📄 PDF Link',
      'pdf_structural_global': '📄 PDF Link (Page)',
      'url': '🌐 URL',
      'text': '📝 Text',
      'qr': '🔳 QR Code',
      'pdf_widget_uri': '📄 PDF Widget',
      'pdf_widget_launch': '📄 PDF Launch',
      'pdf_widget_gotor': '📄 PDF GoTo',
    };
    
    return typeMap[linkType] || linkType.toUpperCase() + ' Link';
  };

  // NEW: Get appropriate icon for link type
  const getLinkIcon = (linkType: string) => {
    const iconMap: { [key: string]: string } = {
      'pdf_structural': '📄',
      'pdf_structural_global': '📄',
      'url': '🌐',
      'text': '📝',
      'qr': '🔳',
    };
    
    return iconMap[linkType] || '🔗';
  };

  // NEW: Get button color based on link type
  const getLinkColor = (linkType: string) => {
    const colorMap: { [key: string]: string } = {
      'pdf_structural': 'bg-purple-500 hover:bg-purple-600',
      'pdf_structural_global': 'bg-purple-400 hover:bg-purple-500',
      'url': 'bg-blue-500 hover:bg-blue-600',
      'text': 'bg-gray-500 hover:bg-gray-600',
      'qr': 'bg-green-500 hover:bg-green-600',
    };
    
    return colorMap[linkType] || 'bg-indigo-500 hover:bg-indigo-600';
  };

  return (
    <div className="p-8 space-y-8 bg-white">
      {/* Header */}
      <div className="flex justify-between items-center border-b-2 border-gray-200 pb-6">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Extraction Results</h2>
          <p className="text-gray-600 mt-2">Analysis of embedded images in your PDF</p>
        </div>
        <button
          onClick={downloadReport}
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
        >
          📥 Download Report
        </button>
      </div>

      {/* Pages */}
      {result.map((page, pageIdx) => (
        <div key={pageIdx} className="bg-white rounded-xl p-6 border border-gray-200">
          <h4 className="text-xl font-semibold mb-4">
            Page {page.page} - {page.images.length} image(s)
          </h4>

          <div className="flex flex-wrap gap-4">
            {page.images.map((img, idx) => {
              const isFailed = failedImages.has(img.url);

              return (
                <div
                  key={idx}
                  className="border p-4 rounded-lg min-w-[250px] flex flex-col items-center bg-gray-50 shadow-sm"
                >
                  {/* Image */}
                  <div className="w-full h-48 relative mb-3 bg-gray-100 flex items-center justify-center rounded border">
                    {isFailed ? (
                      <div className="text-gray-500 text-center">Failed to load image</div>
                    ) : (
                      <Image
                        src={img.url}
                        alt={img.filename}
                        fill
                        style={{ objectFit: "contain" }}
                        className="cursor-pointer"
                        onError={() => handleImageError(img.url)}
                      />
                    )}
                  </div>

                  {/* Filename */}
                  <div className="text-sm text-gray-700 break-all text-center font-mono mb-2">
                    {img.filename}
                  </div>

                  {/* Image area info - NEW */}
                  {img.image_area && (
                    <div className="text-xs text-gray-500 mb-2 text-center">
                      Area: [{img.image_area.map(n => n.toFixed(1)).join(', ')}]
                    </div>
                  )}

                  {/* Clickable link badge */}
                  <div className={`text-xs font-bold mt-1 mb-3 px-2 py-1 rounded ${
                    img.clickable_links_found 
                      ? "bg-red-100 text-red-700 border border-red-300" 
                      : "bg-green-100 text-green-700 border border-green-300"
                  }`}>
                    {img.clickable_links_found ? "⚠️ Clickable Link(s) Detected" : "✅ No Links Found"}
                  </div>

                  {/* Render all extracted links - UPDATED */}
                  {img.extracted_links && img.extracted_links.length > 0 && (
                    <div className="flex flex-col gap-2 mt-2 w-full">
                      <div className="text-xs font-semibold text-gray-600 text-center">
                        Detected Links ({img.extracted_links.length})
                      </div>
                      {img.extracted_links.map((link, linkIdx) => (
                        <div key={linkIdx} className="flex flex-col gap-1">
                          <button
                            onClick={() => openLink(link.content)}
                            className={`${getLinkColor(link.type)} text-white px-3 py-2 rounded text-sm text-left break-all transition-colors`}
                            title={link.content}
                          >
                            <div className="flex items-center gap-2">
                              <span>{getLinkIcon(link.type)}</span>
                              <span className="flex-1 truncate">{getLinkLabel(link.type)}</span>
                            </div>
                          </button>
                          
                          {/* Link metadata - NEW */}
                          <div className="text-xs text-gray-500 px-1">
                            {link.description && (
                              <div>{link.description}</div>
                            )}
                            {link.confidence && (
                              <div>Confidence: {(link.confidence * 100).toFixed(1)}%</div>
                            )}
                            {link.bbox && (
                              <div>Position: [{link.bbox.map(n => n.toFixed(1)).join(', ')}]</div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* View Image Button */}
                  <button
                    onClick={() => window.open(img.url, "_blank")}
                    className="mt-3 bg-gray-200 hover:bg-gray-300 text-gray-800 px-3 py-2 rounded text-sm w-full transition-colors"
                  >
                    🔍 View Full Image
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}