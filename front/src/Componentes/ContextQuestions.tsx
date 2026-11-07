import type { ContextQuestion } from "../types";

type Props = {
  questions: ContextQuestion[];
  busy: boolean;
  onAnswer: (id: string, answer: boolean | null) => void;
};

const OPTIONS: { label: string; value: boolean | null }[] = [
  { label: "Sí", value: true },
  { label: "No", value: false },
  { label: "No sé", value: null },
];

/** Context questions that narrow the procedures of the picked activity. */
export default function ContextQuestions({ questions, busy, onAnswer }: Props) {
  if (!questions.length) return null;
  return (
    <section className="panel context-card" aria-busy={busy}>
      <h2>Contanos más de tu comercio</h2>
      <p className="small-note">Con cada respuesta descartamos los trámites que no te corresponden.</p>
      {questions.map(question => (
        <div className="context-question" role="group" aria-label={question.text} key={question.id}>
          <span>{question.text}</span>
          <div className="answer-toggle">
            {OPTIONS.map(option => (
              <button key={option.label} type="button" aria-pressed={question.answer === option.value}
                className={question.answer === option.value ? "is-selected" : ""}
                onClick={() => onAnswer(question.id, option.value)}>
                {option.label}
              </button>
            ))}
          </div>
        </div>
      ))}
    </section>
  );
}
