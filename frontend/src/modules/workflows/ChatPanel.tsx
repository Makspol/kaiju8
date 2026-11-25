import { createEffect, createSignal, For, Show } from "solid-js";
import type { WorkflowNode, WorkflowRunResult } from "../../shared/types";

interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  text: string;
}

interface Props {
  triggerNode: WorkflowNode;
  running: boolean;
  onClose: () => void;
  onSend: (input: Record<string, unknown>) => Promise<WorkflowRunResult | null>;
}

function conversationIdFor(node: WorkflowNode): string {
  return `chat-${node.id}`;
}

function extractReply(result: WorkflowRunResult | null): string {
  const chat = result?.output?.chat as { reply?: unknown } | undefined;

  if (typeof chat?.reply === "string" && chat.reply.trim()) {
    return chat.reply;
  }

  if (typeof result?.output?.response === "string") {
    return result.output.response;
  }

  if (result?.status === "success") {
    return "Request completed successfully.";
  }

  return result?.error || "Request failed.";
}

export function ChatPanel(props: Props) {
  const [text, setText] = createSignal("");
  const [messages, setMessages] = createSignal<ChatMessage[]>([]);
  let messagesContainerRef: HTMLDivElement | undefined;

  createEffect(() => {
    messages();
    props.running;

    if (messagesContainerRef) {
      messagesContainerRef.scrollTop = messagesContainerRef.scrollHeight;
    }
  });

  async function send() {
    const message = text().trim();

    if (!message || props.running) return;

    setText("");
    setMessages((items) => [
      ...items,
      { id: crypto.randomUUID(), role: "user", text: message },
    ]);

    const result = await props.onSend({
      message,
      conversation_id: conversationIdFor(props.triggerNode),
    });

    setMessages((items) => [
      ...items,
      {
        id: crypto.randomUUID(),
        role: result?.status === "success" ? "assistant" : "system",
        text: extractReply(result),
      },
    ]);
  }

  return (
    <div class="chat-panel">
      <div class="chat-panel-header">
        <div>
          <strong>Chat Trigger</strong>
          <span>{props.triggerNode.id.slice(0, 8)}</span>
        </div>
        <button class="ghost-button" onClick={props.onClose}>Close</button>
      </div>

      <div ref={messagesContainerRef} class="chat-panel-messages">
        <Show when={messages().length === 0}>
          <div class="subtle">Send a message to start this workflow.</div>
        </Show>
        <For each={messages()}>
          {(message) => (
            <div class={`chat-message ${message.role}`}>
              <span>{message.role}</span>
              <p>{message.text}</p>
            </div>
          )}
        </For>
        <Show when={props.running}>
          <div class="chat-message system">
            <span>system</span>
            <p>Processing...</p>
          </div>
        </Show>
      </div>

      <div class="chat-panel-input">
        <input
          value={text()}
          disabled={props.running}
          placeholder="Type a message..."
          onInput={(event) => setText(event.currentTarget.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") void send();
          }}
        />
        <button
          class="primary-button"
          disabled={props.running || !text().trim()}
          onClick={send}
        >
          Send
        </button>
      </div>
    </div>
  );
}
