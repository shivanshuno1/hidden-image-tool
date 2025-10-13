"use client";

import { useState } from 'react';

// Define the type for the result prop
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

  const handleImageLoad = (imageUrl: string) => {
    setLoadedImages(prev => new Set(prev).add(imageUrl));
    setFailedImages(prev => {
      const newSet = new Set(prev);
      newSet.delete(imageUrl);
      return newSet;
    });
  };

  const handleImageError = (imageUrl: string) => {
    console.error('Failed to load image:', imageUrl);
    setFailedImages(prev => new Set(prev).add(imageUrl));
    setLoadedImages(prev => {
      const newSet = new Set(prev);
      newSet.delete(imageUrl);
      return newSet;
    });
  };

  // Function to open image in new tab
  const openImageInNewTab = (url: string) => {
    window.open(url, '_blank');
  };

  // Filter images to only show those with clickable_link_found = true
  const filteredResult = result.map(page => ({
    ...page,
    images: page.images.filter(image => image.clickable_link_found)
  }));

  // Check if there are any images with clickable links in the result
  const totalClickableImages = filteredResult.reduce((acc, page) => acc + page.images.length, 0);
  const totalAllImages = result.reduce((acc, page) => acc + page.images.length, 0);

  return (
    <div className="p-8 space-y-8 bg-white">
      {/* Header Section */}
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

      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-blue-50 border-2 border-blue-200 rounded-2xl p-6 text-center">
          <div className="text-3xl font-bold text-blue-700">{result.length}</div>
          <div className="text-blue-800 font-semibold mt-2">Pages Scanned</div>
        </div>
        <div className="bg-green-50 border-2 border-green-200 rounded-2xl p-6 text-center">
          <div className="text-3xl font-bold text-green-700">{totalAllImages}</div>
          <div className="text-green-800 font-semibold mt-2">Total Images Found</div>
        </div>
        <div className="bg-purple-50 border-2 border-purple-200 rounded-2xl p-6 text-center">
          <div className="text-3xl font-bold text-purple-700">{totalClickableImages}</div>
          <div className="text-purple-800 font-semibold mt-2">Clickable Images</div>
        </div>
        <div className="bg-orange-50 border-2 border-orange-200 rounded-2xl p-6 text-center">
          <div className="text-3xl font-bold text-orange-700">
            {totalAllImages > 0 ? ((totalClickableImages / totalAllImages) * 100).toFixed(1) : 0}%
          </div>
          <div className="text-orange-800 font-semibold mt-2">Detection Rate</div>
        </div>
      </div>

      {/* Main Results Section */}
      {totalClickableImages === 0 ? (
        <div className="bg-yellow-50 border-2 border-yellow-200 rounded-2xl p-8 text-center">
          <div className="text-5xl mb-4">🔍</div>
          <h3 className="text-2xl font-bold text-yellow-800 mb-4">No Clickable Images Found</h3>
          <div className="text-yellow-700 space-y-2">
            <p className="text-lg">
              The scanner analyzed <span className="font-bold">{totalAllImages} images</span> across{' '}
              <span className="font-bold">{result.length} pages</span>.
            </p>
            <p className="text-lg">
              No images with clickable links were detected in this PDF.
            </p>
          </div>
          <div className="mt-6 bg-white border border-yellow-300 rounded-xl p-4 max-w-2xl mx-auto">
            <p className="text-gray-700 text-sm">
              💡 <strong>Note:</strong> This is a good security finding! No embedded images contain clickable links that could pose security risks.
            </p>
          </div>
        </div>
      ) : (
        <>
          {/* Images with Clickable Links */}
          <div className="bg-red-50 border-2 border-red-200 rounded-2xl p-6">
            <div className="flex items-center space-x-3 mb-6">
              <div className="bg-red-500 p-2 rounded-lg">
                <span className="text-white font-bold text-lg">⚠️</span>
              </div>
              <div>
                <h3 className="text-2xl font-bold text-red-800">Security Alert: Clickable Images Found</h3>
                <p className="text-red-700">These images contain clickable links that may pose security risks</p>
              </div>
            </div>

            {/* Scrollable container for all pages */}
            <div className="space-y-6 max-h-[800px] overflow-y-auto pr-4 custom-scrollbar">
              {filteredResult.map((page, pageIndex) => (
                page.images.length > 0 && (
                  <div key={pageIndex} className="bg-white rounded-xl p-6 border border-red-300">
                    {/* Page Header */}
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-xl font-semibold text-gray-900 flex items-center">
                        <span className="bg-gray-600 text-white rounded-full w-8 h-8 flex items-center justify-center mr-3">
                          {page.page}
                        </span>
                        Page {page.page} - {page.images.length} clickable image(s)
                      </h4>
                      <span className="bg-red-500 text-white px-3 py-1 rounded-full text-sm font-bold">
                        Page {page.page}
                      </span>
                    </div>
                    
                    {/* Horizontal scrollable images container */}
                    <div className="overflow-x-auto pb-4">
                      <div className="flex space-x-6 min-w-max">
                        {page.images.map((image, imageIndex) => {
                          const isFailed = failedImages.has(image.url);
                          
                          return (
                            <div 
                              key={imageIndex} 
                              className="border-2 border-red-300 rounded-xl p-4 bg-white shadow-sm w-80 flex-shrink-0 flex flex-col"
                            >
                              {/* Image Container */}
                              <div className="mb-4 bg-gray-100 rounded-lg p-2 flex items-center justify-center min-h-[200px] max-h-[200px]">
                                {isFailed ? (
                                  <div className="text-center text-gray-500">
                                    <div className="text-4xl mb-2">❌</div>
                                    <p className="text-sm">Failed to load image</p>
                                  </div>
                                ) : (
                                  <div 
                                    className="cursor-pointer w-full h-full flex items-center justify-center"
                                    onClick={() => openImageInNewTab(image.url)}
                                    title="Click to view full image in new tab"
                                  >
                                    <img 
                                      src={image.url}
                                      alt={image.filename}
                                      className="max-w-full max-h-full object-contain"
                                      onLoad={() => handleImageLoad(image.url)}
                                      onError={() => handleImageError(image.url)}
                                    />
                                  </div>
                                )}
                              </div>
                              
                              {/* Image Details */}
                              <div className="space-y-3 mt-auto">
                                <div>
                                  <div className="text-sm font-medium text-gray-700 mb-1">Filename:</div>
                                  <div className="text-sm text-gray-900 font-mono bg-gray-100 px-3 py-2 rounded break-all">
                                    {image.filename}
                                  </div>
                                </div>
                                
                                <div className="flex justify-between items-center">
                                  <span className="text-sm font-medium text-gray-700">Clickable Link:</span>
                                  <span className="bg-red-500 text-white px-3 py-1 rounded-full text-sm font-bold flex items-center">
                                    ⚠️ YES
                                  </span>
                                </div>
                                
                                <div>
                                  <div className="text-sm font-medium text-gray-700 mb-1">Image URL:</div>
                                  <div 
                                    className="text-sm text-blue-600 underline cursor-pointer break-all hover:text-blue-800"
                                    onClick={() => openImageInNewTab(image.url)}
                                    title="Click to open image URL"
                                  >
                                    {image.url}
                                  </div>
                                </div>

                                {image.size && (
                                  <div className="text-xs text-gray-500">
                                    Size: {(image.size / 1024).toFixed(1)} KB
                                  </div>
                                )}
                                
                                <button
                                  onClick={() => openImageInNewTab(image.url)}
                                  className="w-full bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded-lg text-sm font-medium transition-colors mt-2 flex items-center justify-center"
                                >
                                  🔍 View Full Image
                                </button>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                )
              ))}
            </div>
          </div>
        </>
      )}

      {/* Security Recommendations */}
      <div className="bg-blue-50 border-2 border-blue-200 rounded-2xl p-6">
        <h3 className="text-xl font-bold text-blue-900 mb-4">🔒 Security Recommendations</h3>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="bg-white rounded-xl p-4 border border-blue-200">
            <h4 className="font-semibold text-blue-800 mb-2">If Clickable Images Found:</h4>
            <ul className="text-blue-700 text-sm space-y-1">
              <li>• Verify the destination URLs are safe</li>
              <li>• Consider removing suspicious links</li>
              <li>• Warn users about potential risks</li>
            </ul>
          </div>
          <div className="bg-white rounded-xl p-4 border border-blue-200">
            <h4 className="font-semibold text-blue-800 mb-2">If No Clickable Images:</h4>
            <ul className="text-blue-700 text-sm space-y-1">
              <li>• Your PDF appears secure</li>
              <li>• No immediate action required</li>
              <li>• Continue regular security practices</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Add custom scrollbar styles */}
      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #f1f1f1;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #c1c1c1;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #a8a8a8;
        }
      `}</style>
    </div>
  );
}