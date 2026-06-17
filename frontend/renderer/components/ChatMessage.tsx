import type { ChatMessageData, QuestionLocalState } from "../chat/chat-types";
import type { IRQuestionPayload } from "../ipc/types";
import AssumptionTag from "./AssumptionTag";
import DiffSummary from "./DiffSummary";

interface ChatMessageProps {
  message: ChatMessageData;
  questionStates: Record<string, QuestionLocalState>;
  onQuestionAnswerChange: (questionId: string, answer: string) => void;
  onQuestionAccept: (questionId: string) => void;
}

function BlockingQuestionRow({
  question,
  state,
  onAnswerChange,
  onAccept,
}: {
  question: IRQuestionPayload;
  state: QuestionLocalState;
  onAnswerChange: (answer: string) => void;
  onAccept: () => void;
}) {
  const displayStatus = state.status;

  return (
    <div className="blocking-question">
      <div className="blocking-question-text">{question.text}</div>
      {displayStatus === "open" ? (
        <div className="blocking-question-row">
          <input
            className="blocking-question-input"
            type="text"
            value={state.answer}
            placeholder="Your answer…"
            onChange={(e) => onAnswerChange(e.target.value)}
          />
          <button className="blocking-question-accept" type="button" onClick={onAccept}>
            Accept
          </button>
        </div>
      ) : (
        <div className="blocking-question-answered">
          Answered: {state.answer || question.answer || "—"}
        </div>
      )}
    </div>
  );
}

export default function ChatMessage({
  message,
  questionStates,
  onQuestionAnswerChange,
  onQuestionAccept,
}: ChatMessageProps) {
  const label = message.role === "user" ? "You" : "CopilotCAD";
  const blockingQuestions =
    message.intent?.questions?.filter((q) => q.blocking && q.status === "open") ?? [];

  return (
    <div className={`chat-message chat-message-${message.role}`}>
      <div className="chat-message-label">{label}</div>

      {message.kind === "compile_result" && message.intent ? (
        <div className="chat-message-body">
          <div>{message.intent.summary || message.text || "Intent compiled."}</div>
          {message.intent.assumptions && message.intent.assumptions.length > 0 && (
            <div className="assumption-list">
              {message.intent.assumptions.map((assumption) => (
                <AssumptionTag key={assumption.id} assumption={assumption} />
              ))}
            </div>
          )}
          {message.execution && <DiffSummary execution={message.execution} />}
          {message.execution?.problems && message.execution.problems.length > 0 && (
            <ul className="inline-problems">
              {message.execution.problems.map((problem) => (
                <li key={problem.id} className={`inline-problem inline-problem-${problem.severity}`}>
                  {problem.message}
                </li>
              ))}
            </ul>
          )}
          {blockingQuestions.map((question) => {
            const state = questionStates[question.id] ?? {
              status: question.status ?? "open",
              answer: question.answer ?? "",
            };
            return (
              <BlockingQuestionRow
                key={question.id}
                question={question}
                state={state}
                onAnswerChange={(answer) => onQuestionAnswerChange(question.id, answer)}
                onAccept={() => onQuestionAccept(question.id)}
              />
            );
          })}
        </div>
      ) : (
        <div className="chat-message-body">{message.text}</div>
      )}
    </div>
  );
}
