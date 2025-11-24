"use client";

import { useState } from "react";
import Image from "next/image";

type LinkInfo = {
  type: string;
  content: string;
  description?: string;
};

type ImageInfo = {
  filename: string;
  url: string;
  clickable_link_found: boolean;
  extracted_links?: LinkInfo[];
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
              const firstLink = img.extracted_links?.[0]?.content; // ✅ Safe optional chaining

              return (
                <div
                  key={idx}
                  className="border p-2 rounded-lg min-w-[200px] flex flex-col items-center"
                >
                  {/* Image */}
                  <div className="w-full h-48 relative mb-2 bg-gray-100 flex items-center justify-center">
                    {isFailed ? (
                      <div className="text-gray-500 text-center">Failed to load image</div>
                    ) : (
                      <Image
                        src={img.url}
                        alt={img.filename}
                        fill
                        style={{ objectFit: "contain" }}
                        className="cursor-pointer"
                        onClick={() => firstLink && openLink(firstLink)}
                        onError={() => handleImageError(img.url)}
                      />
                    )}
                  </div>

                  {/* Filename */}
                  <div className="text-sm text-gray-700 break-all text-center">{img.filename}</div>

                  {/* Clickable link badge */}
                  <div className="text-xs text-red-600 font-bold mt-1">
                    {img.clickable_link_found ? "⚠️ Clickable Link" : "No Link"}
                  </div>

                  {/* Go to first link if exists */}
                  {firstLink && (
                    <button
                      onClick={() => openLink(firstLink)}
                      className="mt-2 bg-blue-500 text-white px-2 py-1 rounded text-xs"
                    >
                      Go to Link
                    </button>
                  )}

                  {/* View Image Button */}
                  <button
                    onClick={() => window.open(img.url, "_blank")}
                    className="mt-1 bg-gray-300 hover:bg-gray-400 text-gray-800 px-2 py-1 rounded text-xs"
                  >
                    View Image
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
