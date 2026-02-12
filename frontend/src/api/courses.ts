import { apiFetch } from "./client";
import type { Course, CourseSource } from "../types/workspace";

interface CourseListResponse {
  courses: Course[];
}

export function listCourses(): Promise<Course[]> {
  return apiFetch<CourseListResponse>("/courses").then((r) => r.courses);
}

export function createCourse(data: {
  title: string;
  description: string;
  sources: CourseSource[];
}): Promise<Course> {
  return apiFetch<Course>("/courses", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getCourse(courseId: string): Promise<Course> {
  return apiFetch<Course>(`/courses/${courseId}`);
}

export function deleteCourse(courseId: string): Promise<void> {
  return apiFetch(`/courses/${courseId}`, { method: "DELETE" });
}
