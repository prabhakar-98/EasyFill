import { useState, useEffect, useRef } from "react";
import useAuthStore from "../stores/authStore";
import { apiFetch, apiUpload } from "../lib/api";

const TABS = [
  { key: "personal", label: "Personal", icon: "M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" },
  { key: "professional", label: "Professional", icon: "M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 00.75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 00-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0112 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 01-.673-.38m0 0A2.18 2.18 0 013 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 013.413-.387m7.5 0V5.25A2.25 2.25 0 0013.5 3h-3a2.25 2.25 0 00-2.25 2.25v.894m7.5 0a48.667 48.667 0 00-7.5 0M12 12.75h.008v.008H12v-.008z" },
  { key: "education", label: "Education", icon: "M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342M6.75 15a.75.75 0 100-1.5.75.75 0 000 1.5zm0 0v-3.675A55.378 55.378 0 0112 8.443m-7.007 11.55A5.981 5.981 0 006.75 15.75v-1.5" },
  { key: "experience", label: "Experience", icon: "M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.332A48.36 48.36 0 0012 9.75c-2.551 0-5.056.2-7.5.582V21M3 21h18M12 6.75h.008v.008H12V6.75z" },
  { key: "links", label: "Links", icon: "M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244" },
  { key: "cover_letter", label: "Cover Letter", icon: "M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" },
  { key: "resume", label: "Resume", icon: "M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" },
];

const TONE_OPTIONS = [
  { value: "", label: "Select..." },
  { value: "formal", label: "Formal" },
  { value: "semi-formal", label: "Semi-formal" },
  { value: "conversational", label: "Conversational" },
];

const LENGTH_OPTIONS = [
  { value: "", label: "Select..." },
  { value: "short", label: "Short (150-200 words)" },
  { value: "medium", label: "Medium (250-350 words)" },
  { value: "long", label: "Long (400-500 words)" },
];

const GENDER_OPTIONS = [
  { value: "", label: "Select..." },
  { value: "Male", label: "Male" },
  { value: "Female", label: "Female" },
  { value: "Non-binary", label: "Non-binary" },
  { value: "Prefer not to say", label: "Prefer not to say" },
  { value: "Other", label: "Other" },
];

function Toast({ message, onDismiss }) {
  const isSuccess = message.includes("saved") || message.includes("uploaded") || message.includes("removed");

  useEffect(() => {
    const timer = setTimeout(onDismiss, 3500);
    return () => clearTimeout(timer);
  }, [message, onDismiss]);

  return (
    <div className="fixed bottom-6 right-6 z-50 animate-slide-up">
      <div className={`flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg border ${
        isSuccess
          ? "bg-emerald-50 border-emerald-200 text-emerald-800"
          : "bg-red-50 border-red-200 text-red-800"
      }`}>
        {isSuccess ? (
          <svg className="w-4.5 h-4.5 text-emerald-500" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
          </svg>
        ) : (
          <svg className="w-4.5 h-4.5 text-red-500" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
          </svg>
        )}
        <span className="text-sm font-medium">{message}</span>
        <button onClick={onDismiss} className="ml-2 opacity-50 hover:opacity-100 transition-opacity">
          <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
            <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
          </svg>
        </button>
      </div>
    </div>
  );
}

export default function ProfilePage() {
  const { user } = useAuthStore();
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [activeTab, setActiveTab] = useState("personal");
  const [resume, setResume] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [skillInput, setSkillInput] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [profileLoading, setProfileLoading] = useState(true);
  const fileInputRef = useRef(null);

  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    phone: "",
    location: "",
    headline: "",
    bio: "",
    skills: "",
    institution: "",
    degree: "",
    field_of_study: "",
    gpa: "",
    graduation_year: "",
    company: "",
    job_title: "",
    years_exp: "",
    linkedin: "",
    github: "",
    website: "",
    salary_expectation: "",
    notice_period: "",
    gender: "",
    cl_tone: "",
    cl_length: "",
    cl_motivation: "",
    cl_achievements: "",
    cl_unique_value: "",
    cl_always_mention: "",
    cl_never_mention: "",
  });

  useEffect(() => {
    loadProfile();
  }, []);

  async function loadProfile() {
    setProfileLoading(true);
    try {
      const res = await apiFetch("/api/profile");
      if (!res.ok) return;
      const data = await res.json();
      const pd = data.professional_data || {};
      const edu = pd.education?.[0] || {};
      const work = pd.work_experience?.[0] || {};
      const links = pd.links || {};
      const cl = pd.cover_letter || {};

      setForm({
        first_name: data.first_name || "",
        last_name: data.last_name || "",
        phone: data.phone || "",
        location: data.location || "",
        headline: data.headline || "",
        bio: data.bio || "",
        skills: Array.isArray(pd.skills) ? pd.skills.join(", ") : pd.skills || "",
        institution: edu.institution || "",
        degree: edu.degree || "",
        field_of_study: edu.field_of_study || "",
        gpa: edu.gpa || "",
        graduation_year: edu.graduation_year || "",
        company: work.company || "",
        job_title: work.title || "",
        years_exp: work.years || "",
        linkedin: links.linkedin || "",
        github: links.github || "",
        website: links.website || "",
        salary_expectation: pd.salary_expectation || "",
        notice_period: pd.notice_period || "",
        gender: pd.gender || "",
        cl_tone: cl.tone || "",
        cl_length: cl.length || "",
        cl_motivation: cl.motivation || "",
        cl_achievements: cl.achievements || "",
        cl_unique_value: cl.unique_value || "",
        cl_always_mention: cl.always_mention || "",
        cl_never_mention: cl.never_mention || "",
      });
    } catch {
      // ignore
    } finally {
      setProfileLoading(false);
    }
  }

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSave(e) {
    e.preventDefault();
    setSaving(true);
    setMessage("");

    const body = {
      first_name: form.first_name || null,
      last_name: form.last_name || null,
      phone: form.phone || null,
      location: form.location || null,
      headline: form.headline || null,
      bio: form.bio || null,
      professional_data: {
        skills: form.skills ? form.skills.split(",").map((s) => s.trim()).filter(Boolean) : [],
        education: [
          {
            institution: form.institution,
            degree: form.degree,
            field_of_study: form.field_of_study || null,
            gpa: form.gpa || null,
            graduation_year: form.graduation_year || null,
          },
        ],
        work_experience: [
          {
            company: form.company,
            title: form.job_title,
            years: form.years_exp || null,
            current: true,
          },
        ],
        links: {
          linkedin: form.linkedin || null,
          github: form.github || null,
          website: form.website || null,
        },
        salary_expectation: form.salary_expectation || null,
        notice_period: form.notice_period || null,
        gender: form.gender || null,
        cover_letter: {
          tone: form.cl_tone || null,
          length: form.cl_length || null,
          motivation: form.cl_motivation || null,
          achievements: form.cl_achievements || null,
          unique_value: form.cl_unique_value || null,
          always_mention: form.cl_always_mention || null,
          never_mention: form.cl_never_mention || null,
        },
      },
    };

    try {
      const res = await apiFetch("/api/profile", {
        method: "PUT",
        body: JSON.stringify(body),
      });
      if (res.ok) {
        setMessage("Profile saved!");
      } else {
        const err = await res.json().catch(() => ({}));
        setMessage(err.detail || "Save failed");
      }
    } catch (e) {
      setMessage("Error: " + e.message);
    }
    setSaving(false);
  }

  // --- Skills ---
  const skillsArray = form.skills
    ? form.skills.split(",").map((s) => s.trim()).filter(Boolean)
    : [];

  function removeSkill(index) {
    const updated = skillsArray.filter((_, i) => i !== index);
    setForm({ ...form, skills: updated.join(", ") });
  }

  function addSkill(e) {
    if (e.key === "Enter") {
      e.preventDefault();
      const val = skillInput.trim();
      if (val && !skillsArray.includes(val)) {
        const updated = [...skillsArray, val];
        setForm({ ...form, skills: updated.join(", ") });
      }
      setSkillInput("");
    }
  }

  // --- Resume ---
  async function handleResumeUpload(file) {
    if (!file) return;
    if (file.type !== "application/pdf") {
      setMessage("Only PDF files are allowed");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setMessage("File size must be under 5MB");
      return;
    }
    setUploading(true);
    setMessage("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await apiUpload("/api/resume/upload", formData);
      if (res.ok) {
        const data = await res.json();
        setResume(data);
        setMessage("Resume uploaded!");
      } else {
        const err = await res.json().catch(() => ({}));
        setMessage(err.detail || "Upload failed");
      }
    } catch (e) {
      setMessage("Error: " + e.message);
    }
    setUploading(false);
  }

  async function handleResumeDelete() {
    try {
      const res = await apiFetch("/api/resume", { method: "DELETE" });
      if (res.ok) {
        setResume(null);
        setMessage("Resume removed");
      }
    } catch (e) {
      setMessage("Error: " + e.message);
    }
  }

  function handleResumeDownload() {
    const token = localStorage.getItem("token");
    const base = import.meta.env.VITE_API_URL || "http://localhost:8000";
    window.open(`${base}/api/resume/download?token=${token}`, "_blank");
  }

  function onDrop(e) {
    e.preventDefault();
    setDragOver(false);
    handleResumeUpload(e.dataTransfer.files?.[0]);
  }

  // --- Computed ---
  const initials = (() => {
    const f = form.first_name?.[0] || "";
    const l = form.last_name?.[0] || "";
    if (f || l) return (f + l).toUpperCase();
    return (user?.email?.[0] || "?").toUpperCase();
  })();

  const fullName =
    [form.first_name, form.last_name].filter(Boolean).join(" ") || "Your Name";

  const completedFields = Object.values(form).filter(Boolean).length;
  const totalFields = Object.keys(form).length;
  const completionPct = Math.round((completedFields / totalFields) * 100);

  function formatFileSize(bytes) {
    if (!bytes) return "";
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  }

  if (profileLoading) {
    return (
      <div className="p-8">
        <div className="max-w-4xl mx-auto space-y-6">
          <div className="card p-6 animate-pulse">
            <div className="flex items-start gap-5">
              <div className="w-20 h-20 rounded-full bg-gray-200" />
              <div className="flex-1 space-y-3">
                <div className="h-6 w-48 bg-gray-200 rounded" />
                <div className="h-4 w-32 bg-gray-100 rounded" />
                <div className="h-4 w-64 bg-gray-100 rounded" />
              </div>
            </div>
          </div>
          <div className="card p-6 animate-pulse">
            <div className="space-y-4">
              <div className="h-4 w-24 bg-gray-200 rounded" />
              <div className="h-10 bg-gray-100 rounded" />
              <div className="h-10 bg-gray-100 rounded" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Page header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Profile</h1>
          <p className="text-sm text-gray-500 mt-1">
            This information powers your auto-fill. The more you add, the better it works.
          </p>
        </div>

        {/* Hero Card */}
        <div className="card overflow-hidden">
          <div className="h-1.5 bg-gradient-to-r from-brand-500 via-purple-500 to-pink-500" />
          <div className="p-6 flex items-start gap-5">
            <div
              className="shrink-0 w-20 h-20 rounded-2xl flex items-center justify-center text-white text-2xl font-bold shadow-lg"
              style={{ background: "linear-gradient(135deg, #4f46e5, #7c3aed)" }}
            >
              {initials}
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-xl font-bold text-gray-900 truncate">{fullName}</h2>
              {form.headline && (
                <p className="text-sm text-gray-500 mt-0.5">{form.headline}</p>
              )}
              {form.location && (
                <p className="text-sm text-gray-400 mt-1 flex items-center gap-1">
                  <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                  </svg>
                  {form.location}
                </p>
              )}
              <div className="flex flex-wrap gap-2 mt-3">
                {skillsArray.length > 0 && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-200">
                    {skillsArray.length} skill{skillsArray.length !== 1 && "s"}
                  </span>
                )}
                {form.years_exp && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200">
                    {form.years_exp} yr{form.years_exp !== "1" && "s"} exp
                  </span>
                )}
                {form.degree && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-50 text-purple-700 ring-1 ring-inset ring-purple-200">
                    {form.degree}
                  </span>
                )}
              </div>
            </div>

            {/* Completion ring */}
            <div className="hidden sm:flex flex-col items-center shrink-0">
              <div className="relative w-16 h-16">
                <svg className="w-16 h-16 -rotate-90" viewBox="0 0 64 64">
                  <circle cx="32" cy="32" r="28" fill="none" stroke="#f3f4f6" strokeWidth="4" />
                  <circle
                    cx="32" cy="32" r="28" fill="none"
                    stroke={completionPct >= 80 ? "#10b981" : completionPct >= 50 ? "#f59e0b" : "#6366f1"}
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeDasharray={`${completionPct * 1.76} 176`}
                    className="transition-all duration-700"
                  />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-gray-700">
                  {completionPct}%
                </span>
              </div>
              <span className="text-xs text-gray-400 mt-1">Complete</span>
            </div>
          </div>
        </div>

        {/* Tabbed Form Card */}
        <div className="card">
          {/* Tab bar */}
          <div className="border-b border-gray-100 px-2">
            <nav className="flex -mb-px overflow-x-auto scrollbar-thin">
              {TABS.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`flex items-center gap-2 px-4 py-3.5 text-sm font-medium whitespace-nowrap border-b-2 transition-all duration-200 ${
                    activeTab === tab.key
                      ? "border-brand-600 text-brand-700"
                      : "border-transparent text-gray-400 hover:text-gray-600 hover:border-gray-200"
                  }`}
                >
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
                    <path strokeLinecap="round" strokeLinejoin="round" d={tab.icon} />
                  </svg>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab content */}
          <div className="p-6 animate-fade-in" key={activeTab}>
            {/* Personal */}
            {activeTab === "personal" && (
              <form onSubmit={handleSave} className="space-y-5">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                  <div>
                    <label className="input-label">First Name</label>
                    <input name="first_name" value={form.first_name} onChange={handleChange} className="input-field" placeholder="John" />
                  </div>
                  <div>
                    <label className="input-label">Last Name</label>
                    <input name="last_name" value={form.last_name} onChange={handleChange} className="input-field" placeholder="Doe" />
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                  <div>
                    <label className="input-label">Phone</label>
                    <input name="phone" value={form.phone} onChange={handleChange} className="input-field" placeholder="+1 (555) 123-4567" />
                  </div>
                  <div>
                    <label className="input-label">Location</label>
                    <input name="location" value={form.location} onChange={handleChange} className="input-field" placeholder="San Francisco, CA" />
                  </div>
                </div>
                <div>
                  <label className="input-label">Gender</label>
                  <select name="gender" value={form.gender} onChange={handleChange} className="input-field">
                    {GENDER_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
                <SaveButton saving={saving} />
              </form>
            )}

            {/* Professional */}
            {activeTab === "professional" && (
              <form onSubmit={handleSave} className="space-y-5">
                <div>
                  <label className="input-label">Headline / Current Role</label>
                  <input name="headline" value={form.headline} onChange={handleChange} className="input-field" placeholder="Senior Frontend Engineer" />
                </div>
                <div>
                  <label className="input-label">Bio</label>
                  <textarea name="bio" value={form.bio} onChange={handleChange} rows={3} className="input-field" placeholder="A brief summary about yourself..." />
                </div>
                <div>
                  <label className="input-label">Skills</label>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {skillsArray.map((skill, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-200 animate-fade-in"
                      >
                        {skill}
                        <button
                          type="button"
                          onClick={() => removeSkill(i)}
                          className="text-brand-400 hover:text-brand-700 transition-colors ml-0.5"
                        >
                          <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                            <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                          </svg>
                        </button>
                      </span>
                    ))}
                  </div>
                  <input
                    value={skillInput}
                    onChange={(e) => setSkillInput(e.target.value)}
                    onKeyDown={addSkill}
                    className="input-field"
                    placeholder="Type a skill and press Enter"
                  />
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                  <div>
                    <label className="input-label">Salary Expectation</label>
                    <input name="salary_expectation" value={form.salary_expectation} onChange={handleChange} className="input-field" placeholder="$120,000" />
                  </div>
                  <div>
                    <label className="input-label">Notice Period</label>
                    <input name="notice_period" value={form.notice_period} onChange={handleChange} className="input-field" placeholder="2 weeks" />
                  </div>
                </div>
                <SaveButton saving={saving} />
              </form>
            )}

            {/* Education */}
            {activeTab === "education" && (
              <form onSubmit={handleSave} className="space-y-5">
                <div>
                  <label className="input-label">Institution</label>
                  <input name="institution" value={form.institution} onChange={handleChange} className="input-field" placeholder="Stanford University" />
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                  <div>
                    <label className="input-label">Degree</label>
                    <input name="degree" value={form.degree} onChange={handleChange} className="input-field" placeholder="B.S. Computer Science" />
                  </div>
                  <div>
                    <label className="input-label">Field of Study</label>
                    <input name="field_of_study" value={form.field_of_study} onChange={handleChange} className="input-field" placeholder="Computer Science" />
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                  <div>
                    <label className="input-label">GPA / CGPA</label>
                    <input name="gpa" value={form.gpa} onChange={handleChange} className="input-field" placeholder="3.8" />
                  </div>
                  <div>
                    <label className="input-label">Graduation Year</label>
                    <input name="graduation_year" value={form.graduation_year} onChange={handleChange} className="input-field" placeholder="2024" />
                  </div>
                </div>
                <SaveButton saving={saving} />
              </form>
            )}

            {/* Experience */}
            {activeTab === "experience" && (
              <form onSubmit={handleSave} className="space-y-5">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                  <div>
                    <label className="input-label">Company</label>
                    <input name="company" value={form.company} onChange={handleChange} className="input-field" placeholder="Acme Inc." />
                  </div>
                  <div>
                    <label className="input-label">Job Title</label>
                    <input name="job_title" value={form.job_title} onChange={handleChange} className="input-field" placeholder="Software Engineer" />
                  </div>
                </div>
                <div>
                  <label className="input-label">Years of Experience</label>
                  <input name="years_exp" value={form.years_exp} onChange={handleChange} className="input-field" placeholder="3" />
                </div>
                <SaveButton saving={saving} />
              </form>
            )}

            {/* Links */}
            {activeTab === "links" && (
              <form onSubmit={handleSave} className="space-y-5">
                <LinkField
                  label="LinkedIn"
                  name="linkedin"
                  value={form.linkedin}
                  onChange={handleChange}
                  placeholder="https://linkedin.com/in/..."
                  icon="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"
                />
                <LinkField
                  label="GitHub"
                  name="github"
                  value={form.github}
                  onChange={handleChange}
                  placeholder="https://github.com/..."
                  icon="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"
                />
                <LinkField
                  label="Website / Portfolio"
                  name="website"
                  value={form.website}
                  onChange={handleChange}
                  placeholder="https://yoursite.com"
                  strokeIcon="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418"
                />
                <SaveButton saving={saving} />
              </form>
            )}

            {/* Cover Letter */}
            {activeTab === "cover_letter" && (
              <form onSubmit={handleSave} className="space-y-5">
                <div className="rounded-lg bg-brand-50/50 border border-brand-100 px-4 py-3 mb-1">
                  <p className="text-sm text-brand-700">
                    These preferences help EasyFill generate tailored cover letter responses when forms ask for one.
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                  <div>
                    <label className="input-label">Preferred Tone</label>
                    <select name="cl_tone" value={form.cl_tone} onChange={handleChange} className="input-field">
                      {TONE_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="input-label">Preferred Length</label>
                    <select name="cl_length" value={form.cl_length} onChange={handleChange} className="input-field">
                      {LENGTH_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="input-label">Career Motivation</label>
                  <textarea
                    name="cl_motivation"
                    value={form.cl_motivation}
                    onChange={handleChange}
                    rows={3}
                    className="input-field"
                    placeholder="Why are you looking for new opportunities? What drives your career decisions?"
                  />
                </div>

                <div>
                  <label className="input-label">Key Achievements</label>
                  <textarea
                    name="cl_achievements"
                    value={form.cl_achievements}
                    onChange={handleChange}
                    rows={3}
                    className="input-field"
                    placeholder="Top accomplishments you'd like highlighted (e.g. 'Led migration to microservices, reducing latency by 40%')"
                  />
                </div>

                <div>
                  <label className="input-label">What Makes You Unique</label>
                  <textarea
                    name="cl_unique_value"
                    value={form.cl_unique_value}
                    onChange={handleChange}
                    rows={2}
                    className="input-field"
                    placeholder="Your unique value proposition — what sets you apart from other candidates?"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                  <div>
                    <label className="input-label">Always Mention</label>
                    <textarea
                      name="cl_always_mention"
                      value={form.cl_always_mention}
                      onChange={handleChange}
                      rows={2}
                      className="input-field"
                      placeholder="Things to always include (e.g. 'open source contributions', 'remote work experience')"
                    />
                  </div>
                  <div>
                    <label className="input-label">Never Mention</label>
                    <textarea
                      name="cl_never_mention"
                      value={form.cl_never_mention}
                      onChange={handleChange}
                      rows={2}
                      className="input-field"
                      placeholder="Things to avoid mentioning (e.g. 'specific company names from past roles')"
                    />
                  </div>
                </div>

                <SaveButton saving={saving} />
              </form>
            )}

            {/* Resume */}
            {activeTab === "resume" && (
              <div className="space-y-5">
                {!resume ? (
                  <div
                    onDrop={onDrop}
                    onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                    onDragLeave={() => setDragOver(false)}
                    onClick={() => fileInputRef.current?.click()}
                    className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all duration-200 ${
                      dragOver
                        ? "border-brand-400 bg-brand-50/50 scale-[1.01]"
                        : "border-gray-200 hover:border-gray-300 hover:bg-gray-50/50"
                    }`}
                  >
                    <div className="mx-auto w-14 h-14 rounded-2xl bg-gray-100 flex items-center justify-center mb-4">
                      <svg className="w-7 h-7 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                      </svg>
                    </div>
                    <p className="text-sm font-medium text-gray-700">
                      {uploading ? "Uploading..." : "Drop your resume here or click to browse"}
                    </p>
                    <p className="text-xs text-gray-400 mt-1.5">PDF only, max 5MB</p>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,application/pdf"
                      className="hidden"
                      onChange={(e) => handleResumeUpload(e.target.files?.[0])}
                    />
                  </div>
                ) : (
                  <div className="card p-5 flex items-center gap-4 animate-fade-in">
                    <div className="w-12 h-12 rounded-xl bg-red-50 flex items-center justify-center shrink-0">
                      <svg className="w-6 h-6 text-red-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{resume.file_name}</p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {formatFileSize(resume.file_size_bytes)}
                        {resume.created_at && " · " + new Date(resume.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <button onClick={handleResumeDownload} className="btn-secondary text-xs px-3 py-1.5">
                        Download
                      </button>
                      <button
                        onClick={handleResumeDelete}
                        className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-red-600 border border-red-200 rounded-lg hover:bg-red-50 transition-colors"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {message && <Toast message={message} onDismiss={() => setMessage("")} />}
    </div>
  );
}

function SaveButton({ saving }) {
  return (
    <div className="flex justify-end pt-2">
      <button type="submit" disabled={saving} className="btn-primary">
        {saving ? (
          <span className="flex items-center gap-2">
            <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Saving...
          </span>
        ) : (
          "Save changes"
        )}
      </button>
    </div>
  );
}

function LinkField({ label, name, value, onChange, placeholder, icon, strokeIcon }) {
  return (
    <div>
      <label className="input-label">{label}</label>
      <div className="flex">
        <span className="inline-flex items-center px-3 rounded-l-lg border border-r-0 border-gray-200 bg-gray-50 text-gray-400">
          {strokeIcon ? (
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
              <path strokeLinecap="round" strokeLinejoin="round" d={strokeIcon} />
            </svg>
          ) : (
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path d={icon} />
            </svg>
          )}
        </span>
        <input
          name={name}
          value={value}
          onChange={onChange}
          className="flex-1 px-3.5 py-2.5 border border-gray-200 rounded-r-lg text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all duration-200"
          placeholder={placeholder}
        />
      </div>
    </div>
  );
}
