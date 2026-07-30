import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client";

interface LessonSummary {
  key: string;
  title: string;
  vuln_class: string;
  owasp_web: string;
  owasp_api: string;
  has_probe: boolean;
  status: string;
}

export default function Lessons() {
  const [lessons, setLessons] = useState<LessonSummary[]>([]);

  useEffect(() => {
    void (async () => {
      const resp = await api("/api/lessons");
      if (resp.ok) setLessons(await resp.json());
    })();
  }, []);

  return (
    <section>
      <h2>Vulnerability lessons</h2>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
          gap: 12,
        }}
      >
        {lessons.map((lesson) => (
          <Link
            key={lesson.key}
            to={`/lessons/${lesson.key}`}
            style={{
              border: "1px solid #ccc",
              borderRadius: 8,
              padding: 12,
              textDecoration: "none",
              color: "inherit",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <strong>{lesson.title}</strong>
              {lesson.status === "completed" && (
                <span aria-label="completed" title="completed">
                  ✓
                </span>
              )}
            </div>
            <div style={{ fontSize: 12, opacity: 0.7 }}>
              {lesson.owasp_web}
              {lesson.owasp_api ? ` · ${lesson.owasp_api}` : ""}
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
