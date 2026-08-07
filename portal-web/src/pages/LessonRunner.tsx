import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../api/client";

interface LessonDetail {
  key: string;
  title: string;
  owasp_web: string;
  owasp_api: string;
  has_probe: boolean;
  concept: string;
  fix: string;
  verified_by: string;
  probe_explain: string;
  status: string;
}

const STEPS = ["Concept", "Try it", "The fix", "Complete"];

export default function LessonRunner() {
  const { key } = useParams();
  const [lesson, setLesson] = useState<LessonDetail | null>(null);
  const [step, setStep] = useState(0);
  const [probe, setProbe] = useState<unknown>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    void (async () => {
      const resp = await api(`/api/lessons/${key}`);
      if (resp.ok) {
        const detail: LessonDetail = await resp.json();
        setLesson(detail);
        setDone(detail.status === "completed");
      }
    })();
  }, [key]);

  async function runProbe() {
    const resp = await api(`/api/lessons/${key}/try`, { method: "POST" });
    if (resp.ok) setProbe(await resp.json());
  }

  async function markComplete() {
    const resp = await api(`/api/lessons/${key}/complete`, { method: "POST" });
    if (resp.ok) setDone(true);
  }

  if (!lesson) return <p>Loading…</p>;

  return (
    <section>
      <p>
        <Link to="/lessons">← All lessons</Link>
      </p>
      <h2>
        {lesson.title} {done && <span aria-label="completed">✓</span>}
      </h2>

      <nav>
        {STEPS.map((label, i) => (
          <button key={label} onClick={() => setStep(i)} disabled={i === step} style={{ marginRight: 8 }}>
            {label}
          </button>
        ))}
      </nav>

      {step === 0 && (
        <div>
          <p>{lesson.concept}</p>
          <p>
            <em>
              {lesson.owasp_web}
              {lesson.owasp_api ? ` · ${lesson.owasp_api}` : ""}
            </em>
          </p>
        </div>
      )}

      {step === 1 && (
        <div>
          {lesson.has_probe ? (
            <>
              <p>{lesson.probe_explain}</p>
              <button onClick={() => void runProbe()}>Run safe observation</button>
              {probe != null && (
                <pre style={{ background: "#f4f4f4", padding: 12, overflowX: "auto" }}>
                  {JSON.stringify(probe, null, 2)}
                </pre>
              )}
            </>
          ) : (
            <p>This lesson is concept-only; there is no safe live probe.</p>
          )}
        </div>
      )}

      {step === 2 && (
        <div>
          <p>{lesson.fix}</p>
          <p>
            <small>Verified by: {lesson.verified_by}</small>
          </p>
        </div>
      )}

      {step === 3 && (
        <div>
          {done ? (
            <p>Completed ✓</p>
          ) : (
            <button onClick={() => void markComplete()}>Mark complete</button>
          )}
        </div>
      )}
    </section>
  );
}
