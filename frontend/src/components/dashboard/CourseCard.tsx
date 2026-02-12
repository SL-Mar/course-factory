import type { Course } from "../../types/workspace";

interface CourseCardProps {
  course: Course;
  onClick: () => void;
}

export function CourseCard({ course, onClick }: CourseCardProps) {
  return (
    <button
      onClick={onClick}
      className="rounded-xl border border-surface-border bg-surface-card p-5 text-left transition-colors hover:border-gray-600"
    >
      <h3 className="text-sm font-semibold text-gray-200 truncate">
        {course.title}
      </h3>
      {course.description && (
        <p className="mt-1.5 text-xs text-gray-500 line-clamp-2">
          {course.description}
        </p>
      )}
      <div className="mt-3 flex flex-wrap gap-1.5">
        {course.sources.map((s, i) => (
          <span
            key={i}
            className="rounded-full bg-surface px-2 py-0.5 text-[10px] font-medium text-gray-400 border border-surface-border"
          >
            {s.type}
          </span>
        ))}
      </div>
    </button>
  );
}
