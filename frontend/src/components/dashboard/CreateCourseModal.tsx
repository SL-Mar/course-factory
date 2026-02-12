import { useState } from "react";
import { createCourse } from "../../api/courses";
import type { CourseSource } from "../../types/workspace";
import { cn } from "../../utils/cn";

interface CreateCourseModalProps {
  onClose: () => void;
  onCreated: (courseId: string) => void;
}

type SourceType = "notion" | "github" | "url";

interface SourceDraft {
  type: SourceType;
  id: string;
  owner: string;
  repo: string;
  url: string;
}

const emptySrc = (): SourceDraft => ({
  type: "notion",
  id: "",
  owner: "",
  repo: "",
  url: "",
});

export function CreateCourseModal({
  onClose,
  onCreated,
}: CreateCourseModalProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [sources, setSources] = useState<SourceDraft[]>([emptySrc()]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const addSource = () => setSources([...sources, emptySrc()]);

  const updateSource = (idx: number, patch: Partial<SourceDraft>) => {
    setSources(sources.map((s, i) => (i === idx ? { ...s, ...patch } : s)));
  };

  const removeSource = (idx: number) => {
    setSources(sources.filter((_, i) => i !== idx));
  };

  const toApi = (d: SourceDraft): CourseSource => {
    if (d.type === "notion") return { type: "notion", id: d.id };
    if (d.type === "github")
      return { type: "github", owner: d.owner, repo: d.repo };
    return { type: "url", url: d.url };
  };

  const handleSubmit = async () => {
    if (!title.trim()) {
      setError("Title is required");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const course = await createCourse({
        title: title.trim(),
        description: description.trim(),
        sources: sources
          .filter(
            (s) =>
              s.id.trim() ||
              (s.owner.trim() && s.repo.trim()) ||
              s.url.trim(),
          )
          .map(toApi),
      });
      onCreated(course.id);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create course");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-lg rounded-xl border border-surface-border bg-surface-card p-6">
        <h2 className="text-lg font-semibold text-gray-100 mb-5">
          New Course
        </h2>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-gray-300">
              Title
            </label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Maritime Route Optimization"
              className="w-full rounded-lg border border-surface-border bg-surface px-3 py-2.5 text-gray-100 placeholder-gray-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-gray-300">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              placeholder="Brief description of this course..."
              className="w-full rounded-lg border border-surface-border bg-surface px-3 py-2.5 text-gray-100 placeholder-gray-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 resize-none"
            />
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-300">
                Sources
              </label>
              <button
                onClick={addSource}
                className="text-xs text-indigo-400 hover:text-indigo-300"
              >
                + Add source
              </button>
            </div>
            {sources.map((src, idx) => (
              <div
                key={idx}
                className="rounded-lg border border-surface-border bg-surface p-3 space-y-2"
              >
                <div className="flex items-center gap-2">
                  <select
                    value={src.type}
                    onChange={(e) =>
                      updateSource(idx, {
                        type: e.target.value as SourceType,
                      })
                    }
                    className="rounded-md border border-surface-border bg-surface-card px-2 py-1.5 text-xs text-gray-300 focus:outline-none"
                  >
                    <option value="notion">Notion</option>
                    <option value="github">GitHub</option>
                    <option value="url">URL</option>
                  </select>
                  {sources.length > 1 && (
                    <button
                      onClick={() => removeSource(idx)}
                      className="ml-auto text-xs text-gray-600 hover:text-red-400"
                    >
                      Remove
                    </button>
                  )}
                </div>

                {src.type === "notion" && (
                  <input
                    value={src.id}
                    onChange={(e) =>
                      updateSource(idx, { id: e.target.value })
                    }
                    placeholder="Notion page ID"
                    className="w-full rounded-md border border-surface-border bg-surface-card px-2.5 py-1.5 text-xs text-gray-300 font-mono placeholder-gray-600 focus:border-indigo-500 focus:outline-none"
                  />
                )}
                {src.type === "github" && (
                  <div className="flex gap-2">
                    <input
                      value={src.owner}
                      onChange={(e) =>
                        updateSource(idx, { owner: e.target.value })
                      }
                      placeholder="Owner"
                      className="w-1/2 rounded-md border border-surface-border bg-surface-card px-2.5 py-1.5 text-xs text-gray-300 font-mono placeholder-gray-600 focus:border-indigo-500 focus:outline-none"
                    />
                    <input
                      value={src.repo}
                      onChange={(e) =>
                        updateSource(idx, { repo: e.target.value })
                      }
                      placeholder="Repo"
                      className="w-1/2 rounded-md border border-surface-border bg-surface-card px-2.5 py-1.5 text-xs text-gray-300 font-mono placeholder-gray-600 focus:border-indigo-500 focus:outline-none"
                    />
                  </div>
                )}
                {src.type === "url" && (
                  <input
                    value={src.url}
                    onChange={(e) =>
                      updateSource(idx, { url: e.target.value })
                    }
                    placeholder="https://..."
                    className="w-full rounded-md border border-surface-border bg-surface-card px-2.5 py-1.5 text-xs text-gray-300 font-mono placeholder-gray-600 focus:border-indigo-500 focus:outline-none"
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {error && (
          <p className="mt-3 text-sm text-red-400">{error}</p>
        )}

        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="rounded-lg border border-surface-border px-4 py-2 text-sm text-gray-400 hover:text-gray-200 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={saving}
            className={cn(
              "rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors",
              saving
                ? "opacity-50 cursor-not-allowed"
                : "hover:bg-indigo-500",
            )}
          >
            {saving ? "Creating..." : "Create Course"}
          </button>
        </div>
      </div>
    </div>
  );
}
