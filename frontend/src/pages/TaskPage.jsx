import { useParams, useNavigate } from "react-router-dom";
import BrowserView from "../components/BrowserView";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function TaskPage() {
  const { taskId } = useParams();
  const navigate = useNavigate();

  async function handleClose() {
    try {
      await fetch(`${API_URL}/browser/${taskId}/close`, { method: "POST" });
    } catch {
      // ignore
    }
    navigate("/");
  }

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={handleClose}
            className="text-gray-600 hover:text-gray-900 font-medium"
          >
            &larr; Back
          </button>
          <span className="text-gray-900 font-semibold">
            Task: {taskId.slice(0, 8)}...
          </span>
        </div>
        <span className="text-sm text-green-600 font-medium">Interactive</span>
      </header>

      <div className="flex-1 p-4">
        <div className="max-w-5xl mx-auto">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-3 mb-4 text-sm text-yellow-800">
            You can interact with the browser below. If Google asks for sign-in, log in directly here.
          </div>
          <BrowserView taskId={taskId} interactive={true} />
        </div>
      </div>
    </div>
  );
}
