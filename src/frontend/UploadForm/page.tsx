"use client";

import React, { useRef, useState } from "react";

export default function UploadForm({ onUpload }: { onUpload: (file: File) => void }) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState<string>("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (fileInputRef.current?.files?.[0]) {
      onUpload(fileInputRef.current.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Custom file input area */}
        <div 
          onClick={handleButtonClick}
          className="border-2 border-dashed border-gray-400 rounded-xl p-6 text-center cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-all duration-300"
        >
          <div className="flex flex-col items-center justify-center space-y-3">
            <div className="bg-blue-100 p-3 rounded-full">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <div>
              <p className="text-lg font-semibold text-gray-800">Choose PDF File</p>
              <p className="text-sm text-gray-600 mt-1">Click to browse your files</p>
            </div>
          </div>
          
          {/* Hidden file input */}
          <input 
            type="file" 
            ref={fileInputRef} 
            accept=".pdf" 
            onChange={handleFileChange}
            className="hidden" 
          />
        </div>

        {/* Selected file name display */}
        {fileName && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-3">
            <p className="text-green-800 text-sm font-medium">
              📄 Selected: <span className="font-bold">{fileName}</span>
            </p>
          </div>
        )}

        {/* Upload button */}
        <button 
          type="submit" 
          disabled={!fileName}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-semibold py-3 px-4 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
        >
          {fileName ? "Scan PDF for Images" : "Select a file first"}
        </button>

        {/* Help text */}
        <div className="text-center">
          <p className="text-xs text-gray-500">
            Supported format: PDF • Max size: 10MB
          </p>
        </div>
      </form>
    </div>
  );
}