"use client";

import { useState } from 'react';
import UploadForm from '@/frontend/UploadForm/page';
import Loader from '@/frontend/Loader/page';
import ResultViewer from '@/frontend/ResultViewer/page';

type PageInfo = {
  page: number;
  images: Array<{
    filename: string;
    url: string;
    clickable_link_found: boolean;
  }>;
};

export default function HomePage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PageInfo[] | null>(null);

  const handleUpload = async (file: File) => {
    setLoading(true);
    setResult(null);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("https://hidden-backend-1.onrender.com/upload", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Upload failed");

      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      alert("Upload failed, check backend console!");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-gray-800 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-4">
              <div className="bg-blue-600 p-3 rounded-xl">
                <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white">PDF Image Scanner</h1>
                <p className="text-blue-200">Detect hidden images in PDF files</p>
              </div>
            </div>
            <div className="text-blue-200 font-medium">
              Secure • Fast • Accurate
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero Section */}
        <div className="text-center mb-16 bg-white rounded-2xl shadow-xl p-12 border border-gray-300">
          <div className="inline-flex items-center justify-center w-24 h-24 bg-blue-600 rounded-3xl mb-8 shadow-lg">
            <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-6">
            Discover Hidden Images in PDFs
          </h1>
          <p className="text-xl text-gray-700 max-w-2xl mx-auto mb-10 leading-relaxed">
            Upload any PDF file to scan for embedded images and detect potential security risks with clickable links.
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          <div className="bg-white rounded-2xl p-8 border-2 border-gray-300 shadow-lg hover:shadow-xl transition-all duration-300">
            <div className="flex items-center space-x-4">
              <div className="bg-green-500 p-4 rounded-xl">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h3 className="font-bold text-gray-900 text-xl mb-2">Secure Analysis</h3>
                <p className="text-gray-700">Files processed locally</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-8 border-2 border-gray-300 shadow-lg hover:shadow-xl transition-all duration-300">
            <div className="flex items-center space-x-4">
              <div className="bg-blue-600 p-4 rounded-xl">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <h3 className="font-bold text-gray-900 text-xl mb-2">Fast Processing</h3>
                <p className="text-gray-700">Quick image extraction</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-8 border-2 border-gray-300 shadow-lg hover:shadow-xl transition-all duration-300">
            <div className="flex items-center space-x-4">
              <div className="bg-purple-600 p-4 rounded-xl">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <h3 className="font-bold text-gray-900 text-xl mb-2">Detailed Report</h3>
                <p className="text-gray-700">Comprehensive analysis</p>
              </div>
            </div>
          </div>
        </div>

        {/* Upload Section */}
      {/* Upload Section */}
<div className="bg-white rounded-2xl shadow-2xl border-2 border-gray-300 p-12 mb-12">
  <div className="text-center mb-10">
    <h2 className="text-4xl font-bold text-gray-900 mb-4">Start Scanning</h2>
    <p className="text-gray-700 text-xl">Upload a PDF file to begin the analysis</p>
  </div>
  
  {/* ✅ REPLACED BUTTON WITH DIV */}
  <div className="w-full flex justify-center">
    <div className="max-w-2xl mx-auto">
      <UploadForm onUpload={handleUpload} />
    </div>
  </div>
</div>

        {/* Loading State */}
        {loading && (
          <div className="bg-white rounded-2xl shadow-2xl border-2 border-gray-300 p-12 mb-12">
            <div className="text-center">
              <Loader />
              <p className="text-gray-700 mt-6 text-xl font-medium">Analyzing your PDF file...</p>
            </div>
          </div>
        )}

        {/* Results Section */}
        {result && (
          <div className="bg-white rounded-2xl shadow-2xl border-2 border-gray-300 overflow-hidden mb-12">
            <ResultViewer result={result} />
          </div>
        )}

        {/* Info Section - Only show when no results and not loading */}
        {!result && !loading && (
          <div className="bg-white rounded-2xl p-12 border-2 border-gray-300 shadow-lg mb-12">
            <div className="grid md:grid-cols-2 gap-12">
              <div>
                <h3 className="text-3xl font-bold text-gray-900 mb-8">How it works</h3>
                <ul className="space-y-6 text-gray-800">
                  <li className="flex items-start space-x-4 bg-gray-50 p-6 rounded-xl border border-gray-200">
                    <div className="bg-blue-600 text-white rounded-full p-3 mt-1 flex-shrink-0">
                      <span className="text-lg font-bold">1</span>
                    </div>
                    <div>
                      <span className="text-lg font-semibold">Upload any PDF file securely</span>
                      <p className="text-gray-600 mt-1">Choose your PDF file for analysis</p>
                    </div>
                  </li>
                  <li className="flex items-start space-x-4 bg-gray-50 p-6 rounded-xl border border-gray-200">
                    <div className="bg-blue-600 text-white rounded-full p-3 mt-1 flex-shrink-0">
                      <span className="text-lg font-bold">2</span>
                    </div>
                    <div>
                      <span className="text-lg font-semibold">Automatic image extraction and analysis</span>
                      <p className="text-gray-600 mt-1">Our system scans for embedded images</p>
                    </div>
                  </li>
                  <li className="flex items-start space-x-4 bg-gray-50 p-6 rounded-xl border border-gray-200">
                    <div className="bg-blue-600 text-white rounded-full p-3 mt-1 flex-shrink-0">
                      <span className="text-lg font-bold">3</span>
                    </div>
                    <div>
                      <span className="text-lg font-semibold">Detect images with clickable links</span>
                      <p className="text-gray-600 mt-1">Identify potential security risks</p>
                    </div>
                  </li>
                  <li className="flex items-start space-x-4 bg-gray-50 p-6 rounded-xl border border-gray-200">
                    <div className="bg-blue-600 text-white rounded-full p-3 mt-1 flex-shrink-0">
                      <span className="text-lg font-bold">4</span>
                    </div>
                    <div>
                      <span className="text-lg font-semibold">Download comprehensive report</span>
                      <p className="text-gray-600 mt-1">Get detailed analysis results</p>
                    </div>
                  </li>
                </ul>
              </div>
              <div>
                <h3 className="text-3xl font-bold text-gray-900 mb-8">Supported Features</h3>
                <div className="grid grid-cols-2 gap-4">
                  {[
                    { name: 'PDF Image Extraction', icon: '📄' },
                    { name: 'Link Detection', icon: '🔗' },
                    { name: 'Security Analysis', icon: '🛡️' },
                    { name: 'Batch Processing', icon: '⚡' },
                    { name: 'Detailed Reporting', icon: '📊' },
                    { name: 'Fast Processing', icon: '🚀' }
                  ].map((feature) => (
                    <div 
                      key={feature.name} 
                      className="bg-blue-50 border-2 border-blue-200 rounded-xl p-4 text-center hover:bg-blue-100 transition-colors"
                    >
                      <div className="text-2xl mb-2">{feature.icon}</div>
                      <span className="text-blue-800 font-semibold text-sm">{feature.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white border-t border-gray-700 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-3 mb-4 md:mb-0">
              <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <span className="text-lg font-bold text-white">Secure PDF Analysis Tool</span>
            </div>
            <div className="text-blue-200 text-lg">
              © 2024 PDF Image Scanner. All rights reserved.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}