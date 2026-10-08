import { Fragment, ReactNode } from "react";

// Minimal, safe renderer for the light markdown the agent uses: **bold** and "- " bullet lines.
// Builds React elements (no innerHTML), so model text can never inject HTML.
function inline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith("**") && part.endsWith("**") && part.length > 4 ? (
      <strong key={i}>{part.slice(2, -2)}</strong>
    ) : (
      <Fragment key={i}>{part}</Fragment>
    )
  );
}

export default function RichText({ text }: { text: string }) {
  const lines = text.split("\n");
  const out: ReactNode[] = [];
  let bullets: string[] = [];
  const flush = () => {
    if (bullets.length) {
      out.push(
        <ul key={`ul-${out.length}`}>
          {bullets.map((b, i) => (
            <li key={i}>{inline(b)}</li>
          ))}
        </ul>
      );
      bullets = [];
    }
  };
  lines.forEach((line) => {
    const m = line.match(/^\s*[-*•]\s+(.*)$/);
    if (m) {
      bullets.push(m[1]);
    } else {
      flush();
      if (line.trim()) out.push(<p key={`p-${out.length}`}>{inline(line)}</p>);
    }
  });
  flush();
  return <>{out}</>;
}
