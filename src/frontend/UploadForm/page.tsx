"use client";

import { useState } from 'react';

type UploadFormProps = {
  onUpload: (file: File) => void;
};

export default function UploadForm({ onUpload }: UploadFormProps) {
  const [fileName, setFileName] = useState<string>('');
  const [isDragging, setIsDragging] = useState(false);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setFileName(file.name);
    } else {
      setFileName('');
      alert('Please select a PDF file');
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);

    const file = event.dataTransfer.files?.[0];
    if (file && file.type === 'application/pdf') {
      setFileName(file.name);
    } else {
      setFileName('');
      alert('Please drop a PDF file');
    }
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    const fileInput = document.getElementById('pdf-upload') as HTMLInputElement;
    const file = fileInput.files?.[0];
    if (file) onUpload(file);
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div
          className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-300 ${
            isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400 bg-gray-50'
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => document.getElementById('pdf-upload')?.click()}
        >
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="bg-blue-100 p-4 rounded-2xl">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <p className="text-lg font-semibold text-gray-900">Choose PDF File</p>
            <p className="text-gray-600 mt-1">Click to browse or drag and drop</p>
            <p className="text-gray-500 text-sm mt-2">Maximum file size: 50MB</p>
            {fileName && <p className="text-green-600 font-medium bg-green-50 px-4 py-2 rounded-lg">✅ Selected: {fileName}</p>}
          </div>
          <input id="pdf-upload" type="file" accept=".pdf" onChange={handleFileChange} className="hidden" />
        </div>

        <button 
          type="submit" 
          disabled={!fileName}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-semibold py-4 px-4 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 text-lg"
        >
          {fileName ? '🔍 Scan PDF for Images' : 'Select a PDF File First'}
        </button>
      </form>
    </div>
  );
}
