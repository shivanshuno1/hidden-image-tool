import "./globals.css";

export const metadata = {
  title: "Hidden PDF Image Scanner",
  description: "Detect hidden images in PDF files and scan them for safety.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-900 text-white min-h-screen flex items-center justify-center">
        <main className="w-full max-w-3xl p-6 bg-gray-800 rounded-2xl shadow-lg">
          <h1 className="text-3xl font-bold text-center text-cyan-400 mb-6">
            🔍 Hidden PDF Image Scanner
          </h1>
          {children}
        </main>
      </body>
    </html>
  );
}
