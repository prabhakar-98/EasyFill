import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import useAuthStore from "../stores/authStore";

export default function ConnectExtensionPage() {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [status, setStatus] = useState("waiting");

  const token = localStorage.getItem("token");

  useEffect(() => {
    function onConnected() {
      setStatus("connected");
    }
    window.addEventListener("easyfill-connected", onConnected);

    const timeout = setTimeout(() => {
      if (status === "waiting") setStatus("timeout");
    }, 10000);

    return () => {
      window.removeEventListener("easyfill-connected", onConnected);
      clearTimeout(timeout);
    };
  }, [status]);

  return (
    <div className="p-6 lg:p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Connect Extension</h1>
        <p className="text-sm text-gray-500 mb-8">
          Link the Chrome extension to your account for auto-filling forms.
        </p>

        {/* Hidden element the extension content script reads */}
        <div
          id="easyfill-token"
          data-token={token || ""}
          data-email={user?.email || ""}
          className="hidden"
        />

        <div className="card p-8 text-center">
          {status === "waiting" && (
            <div className="animate-fade-in">
              <div className="mx-auto w-16 h-16 rounded-2xl bg-brand-50 flex items-center justify-center mb-5">
                <svg className="w-8 h-8 text-brand-500 animate-pulse" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M14.25 6.087c0-.355.186-.676.401-.959.221-.29.349-.634.349-1.003 0-1.036-1.007-1.875-2.25-1.875s-2.25.84-2.25 1.875c0 .369.128.713.349 1.003.215.283.401.604.401.959v0a.64.64 0 01-.657.643 48.39 48.39 0 01-4.163-.3c.186 1.613.293 3.25.315 4.907a.656.656 0 01-.658.663v0c-.355 0-.676-.186-.959-.401a1.647 1.647 0 00-1.003-.349c-1.036 0-1.875 1.007-1.875 2.25s.84 2.25 1.875 2.25c.369 0 .713-.128 1.003-.349.283-.215.604-.401.959-.401v0c.31 0 .555.26.532.57a48.039 48.039 0 01-.642 5.056c1.518.19 3.058.309 4.616.354a.64.64 0 00.657-.643v0c0-.355-.186-.676-.401-.959a1.647 1.647 0 01-.349-1.003c0-1.035 1.008-1.875 2.25-1.875 1.243 0 2.25.84 2.25 1.875 0 .369-.128.713-.349 1.003-.215.283-.4.604-.4.959v0c0 .333.277.599.61.58a48.1 48.1 0 005.427-.63 48.05 48.05 0 00.582-4.717.532.532 0 00-.533-.57v0c-.355 0-.676.186-.959.401-.29.221-.634.349-1.003.349-1.035 0-1.875-1.007-1.875-2.25s.84-2.25 1.875-2.25c.37 0 .713.128 1.003.349.283.215.604.401.96.401v0a.656.656 0 00.658-.663 48.422 48.422 0 00-.37-5.36c-1.886.342-3.81.574-5.766.689a.578.578 0 01-.61-.58v0z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Looking for extension...</h3>
              <p className="text-sm text-gray-500 max-w-sm mx-auto">
                Make sure the EasyFill Chrome extension is installed and enabled.
              </p>
              <div className="mt-6 flex justify-center">
                <div className="flex gap-1">
                  {[0, 1, 2].map((i) => (
                    <div
                      key={i}
                      className="w-2 h-2 rounded-full bg-brand-400"
                      style={{ animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite` }}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          {status === "connected" && (
            <div className="animate-slide-up">
              <div className="mx-auto w-16 h-16 rounded-2xl bg-emerald-50 flex items-center justify-center mb-5">
                <svg className="w-8 h-8 text-emerald-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Extension connected!</h3>
              <p className="text-sm text-gray-500 max-w-sm mx-auto mb-6">
                You're all set. Navigate to any job application form and the extension will auto-fill it for you.
              </p>
              <button onClick={() => navigate("/")} className="btn-primary">
                Back to Profile
              </button>
            </div>
          )}

          {status === "timeout" && (
            <div className="animate-fade-in">
              <div className="mx-auto w-16 h-16 rounded-2xl bg-amber-50 flex items-center justify-center mb-5">
                <svg className="w-8 h-8 text-amber-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Extension not detected</h3>
              <p className="text-sm text-gray-500 max-w-sm mx-auto mb-6">
                Make sure the EasyFill extension is installed and enabled in Chrome, then try again.
              </p>
              <div className="flex items-center justify-center gap-3">
                <button onClick={() => setStatus("waiting")} className="btn-primary">
                  Try again
                </button>
                <button onClick={() => navigate("/")} className="btn-secondary">
                  Back to Profile
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Setup instructions */}
        <div className="mt-8">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Setup instructions</h3>
          <div className="space-y-3">
            {[
              { step: "1", text: "Download the EasyFill extension from the Chrome Web Store" },
              { step: "2", text: "Click the extension icon in your toolbar and make sure it's enabled" },
              { step: "3", text: "Return to this page — the extension will connect automatically" },
            ].map(({ step, text }) => (
              <div key={step} className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-brand-50 text-brand-600 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
                  {step}
                </div>
                <p className="text-sm text-gray-600">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
