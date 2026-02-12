import { useState, useEffect } from "react";
import { listCourses } from "../../api/courses";
import type { Course } from "../../types/workspace";
import { CourseCard } from "./CourseCard";
import { CreateCourseModal } from "./CreateCourseModal";

interface DashboardProps {
  onOpenCourse: (courseId: string) => void;
}

export function Dashboard({ onOpenCourse }: DashboardProps) {
  const [courses, setCourses] = useState<Course[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);

  const refresh = () => {
    setLoading(true);
    listCourses()
      .then(setCourses)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    refresh();
  }, []);

  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-100">Courses</h1>
          <p className="mt-1 text-sm text-gray-500">
            Create and manage your course projects
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 transition-colors"
        >
          New Course
        </button>
      </div>

      {loading ? (
        <div className="text-center text-sm text-gray-500 py-20">
          Loading...
        </div>
      ) : courses.length === 0 ? (
        <div className="rounded-xl border border-dashed border-surface-border p-16 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-surface-card">
            <svg
              className="h-6 w-6 text-gray-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25"
              />
            </svg>
          </div>
          <p className="text-sm text-gray-400">No courses yet</p>
          <p className="mt-1 text-xs text-gray-600">
            Click "New Course" to get started
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {courses.map((course) => (
            <CourseCard
              key={course.id}
              course={course}
              onClick={() => onOpenCourse(course.id)}
            />
          ))}
        </div>
      )}

      {showCreate && (
        <CreateCourseModal
          onClose={() => setShowCreate(false)}
          onCreated={(courseId) => {
            setShowCreate(false);
            refresh();
            onOpenCourse(courseId);
          }}
        />
      )}
    </div>
  );
}
