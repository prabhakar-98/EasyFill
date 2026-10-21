import { useState } from "react";
import { useNavigate } from "react-router-dom";

function toEmbedUrl(url) {
  const match = url.match(/\/forms\/d\/e?\/?([a-zA-Z0-9_-]+)/);
  if (!match) return null;
  const formId = match[1];
  if (url.includes("/forms/d/e/")) {
    return `https://docs.google.com/forms/d/e/${formId}/viewform?embedded=true`;
  }
  return `https://docs.google.com/forms/d/${formId}/viewform?embedded=true`;
}

export default function HomePage() {
  const [url, setUrl] = useState("");
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  function handleSubmit(e) {
    e.preventDefault();
    if (!url.trim()) return;

    const embedUrl = toEmbedUrl(url.trim());
    if (!embedUrl) {
      setError("Invalid Google Form URL. Paste a URL like https://docs.google.com/forms/d/...");
      return;
    }

    navigate(`/form?url=${encodeURIComponent(embedUrl)}`);
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-xl">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">EasyFill</h1>
        <p className="text-gray-500 mb-8">Paste a Google Form URL to get started</p>

        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            type="url"
            value={url}
            onChange={(e) => { setUrl(e.target.value); setError(null); }}
            placeholder="https://docs.google.com/forms/..."
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
            required
          />
          <button
            type="submit"
            className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700"
          >
            Go
          </button>
        </form>

        {error && (
          <p className="mt-4 text-red-600 text-sm">{error}</p>
        )}
      </div>
    </div>
  );
}
