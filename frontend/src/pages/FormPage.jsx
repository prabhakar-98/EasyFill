import { useSearchParams, useNavigate } from "react-router-dom";

export default function FormPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const formUrl = searchParams.get("url");

  if (!formUrl) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <p className="text-gray-500">No form URL provided.</p>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 flex flex-col">
      <header className="bg-white border-b border-gray-200 px-4 py-2 flex items-center gap-4 shrink-0">
        <button
          onClick={() => navigate("/")}
          className="text-gray-600 hover:text-gray-900 font-medium text-sm"
        >
          &larr; Back
        </button>
        <span className="text-gray-900 font-semibold text-sm truncate">
          EasyFill
        </span>
      </header>

      <iframe
        src={formUrl}
        title="Google Form"
        className="flex-1 w-full border-0"
        frameBorder="0"
        marginHeight="0"
        marginWidth="0"
      />
    </div>
  );
}
