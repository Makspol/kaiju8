interface NodeIconProps {
  type: string;
  category?: string;
}

const CATEGORY_COLOR: Record<string, string> = {
  trigger: "mint",
  ai: "violet",
  transform: "sky",
  logic: "amber",
  action: "blue",
  output: "green",
};

const TYPE_GLYPH: Record<string, string> = {
  "manual.trigger": "▶",
  "chat.trigger": "☷",
  "ai.agent": "◈",
  "transform.edit_fields": "✎",
  "transform.remove_duplicates": "⊘",
  "logic.if": "?",
  "logic.merge": "⇄",
  "action.http_request": "⇡",
  "output.reply": "↩",
};

export function NodeIcon(props: NodeIconProps) {
  const category = () =>
    props.category ?? props.type.split(".")[0];
  const color = () => CATEGORY_COLOR[category()] ?? "mint";
  const glyph = () => TYPE_GLYPH[props.type] ?? "◆";

  return (
    <span class={`node-icon ${color()}`} aria-hidden="true">
      {glyph()}
    </span>
  );
}

interface StatusBadgeProps {
  status: string;
}

export function StatusBadge(props: StatusBadgeProps) {
  return (
    <span class={`status-badge ${props.status}`}>{props.status}</span>
  );
}

interface ExecutionBadgeProps {
  status: string;
}

export function ExecutionBadge(props: ExecutionBadgeProps) {
  return (
    <span class={`execution-badge ${props.status}`}>{props.status}</span>
  );
}
