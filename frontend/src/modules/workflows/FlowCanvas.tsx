import { createSignal, For, Show } from "solid-js";
import { Copy } from "lucide-solid";
import type { WorkflowGraph, WorkflowEdge, CanvasNode, NodeTypeMetadata } from "../../shared/types";
import { NodeIcon } from "../../components/shared";
import { hasInputPort } from "../node-catalog/helpers";
import { AgentNodeCard } from "./AgentNodeCard";

type ConnectingFrom = {
  nodeId: string;
  route?: "true" | "false";
};

interface Props {
  graph: WorkflowGraph;
  selectedNodeId: string;
  onSelectNode: (id: string) => void;
  onOpenNode: (id: string) => void;
  onOpenChat?: (id: string) => void;
  onUpdateGraph: (graph: WorkflowGraph) => void;
  onDuplicateNode: (id: string) => void;
  getNodeMeta?: (type: string) => NodeTypeMetadata | undefined;
}

const NODE_W = 200;
const NODE_H = 90;
const CANVAS_W = 1800;
const CANVAS_H = 1000;

function getPos(node: CanvasNode): { x: number; y: number } {
  const pos = node._pos ?? (node.config as Record<string, unknown>)["_pos"] as { x: number; y: number } | undefined;
  return pos ?? { x: 80, y: 80 };
}

function toCanvasNodes(graph: WorkflowGraph): CanvasNode[] {
  return graph.nodes.map((n, i) => ({
    ...n,
    _pos: (n.config["_pos"] as { x: number; y: number }) ?? {
      x: 80 + (i % 4) * 240,
      y: 80 + Math.floor(i / 4) * 160,
    },
  }));
}

function edgePath(
  from: { x: number; y: number },
  to: { x: number; y: number },
): string {
  const x1 = from.x + NODE_W;
  const y1 = from.y + NODE_H / 2;
  const x2 = to.x;
  const y2 = to.y + NODE_H / 2;
  const cx = (x1 + x2) / 2;
  return `M ${x1} ${y1} C ${cx} ${y1}, ${cx} ${y2}, ${x2} ${y2}`;
}

export function FlowCanvas(props: Props) {
  const [draggingId, setDraggingId] = createSignal<string | null>(null);
  const [dragOffset, setDragOffset] = createSignal({ x: 0, y: 0 });
  const [connectingFrom, setConnectingFrom] = createSignal<ConnectingFrom | null>(null);

  const canvasNodes = () => toCanvasNodes(props.graph);

  function nodeById(id: string): CanvasNode | undefined {
    return canvasNodes().find((n) => n.id === id);
  }

  function onNodeMouseDown(e: MouseEvent, nodeId: string) {
    if (connectingFrom()) return;
    e.stopPropagation();
    const node = nodeById(nodeId);
    if (!node) return;
    const pos = getPos(node);
    setDraggingId(nodeId);
    setDragOffset({ x: e.clientX - pos.x, y: e.clientY - pos.y });
    props.onSelectNode(nodeId);
  }

  function onCanvasMouseMove(e: MouseEvent) {
    const id = draggingId();
    if (!id) return;

    const newX = Math.max(0, Math.min(CANVAS_W - NODE_W, e.clientX - dragOffset().x));
    const newY = Math.max(0, Math.min(CANVAS_H - NODE_H, e.clientY - dragOffset().y));

    const updatedNodes = props.graph.nodes.map((n) =>
      n.id === id
        ? { ...n, config: { ...n.config, _pos: { x: newX, y: newY } } }
        : n,
    );
    props.onUpdateGraph({ ...props.graph, nodes: updatedNodes });
  }

  function onCanvasMouseUp() {
    setDraggingId(null);
  }

  function onOutputHandleClick(e: MouseEvent, nodeId: string, route?: "true" | "false") {
    e.stopPropagation();
    const current = connectingFrom();
    if (current?.nodeId === nodeId && current.route === route) {
      setConnectingFrom(null);
      return;
    }
    setConnectingFrom({ nodeId, route });
  }

  function onNodeClickForConnect(nodeId: string) {
    const from = connectingFrom();
    if (!from || from.nodeId === nodeId) {
      setConnectingFrom(null);
      return;
    }
    const targetType = nodeById(nodeId)?.type ?? "";
    if (!hasInputPort(props.getNodeMeta?.(targetType), targetType)) return;
    const alreadyExists = props.graph.edges.some(
      (e) => e.source === from.nodeId && e.target === nodeId && (e.label ?? e.branch) === from.route,
    );
    if (!alreadyExists) {
      props.onUpdateGraph({
        ...props.graph,
        edges: [
          ...props.graph.edges,
          {
            source: from.nodeId,
            target: nodeId,
            ...(from.route ? { label: from.route } : {}),
          },
        ],
      });
    }
    setConnectingFrom(null);
  }

  function removeEdge(edge: WorkflowEdge) {
    props.onUpdateGraph({
      ...props.graph,
      edges: props.graph.edges.filter(
        (e) => !(e.source === edge.source && e.target === edge.target),
      ),
    });
  }

  function removeNode(nodeId: string) {
    props.onUpdateGraph({
      nodes: props.graph.nodes.filter((n) => n.id !== nodeId),
      edges: props.graph.edges.filter(
        (e) => e.source !== nodeId && e.target !== nodeId,
      ),
      settings: props.graph.settings,
    });
  }

  return (
    <div
      class="canvas-wrap"
      onMouseMove={onCanvasMouseMove}
      onMouseUp={onCanvasMouseUp}
      onClick={() => connectingFrom() && setConnectingFrom(null)}
    >
      <div class="canvas" style={{ width: `${CANVAS_W}px`, height: `${CANVAS_H}px` }}>
        <svg class="edges" width={CANVAS_W} height={CANVAS_H}>
          <For each={props.graph.edges}>
            {(edge) => {
              const fromNode = () => nodeById(edge.source);
              const toNode = () => nodeById(edge.target);
              return (
                <Show when={fromNode() && toNode()}>
                  <g>
                    <path
                      class="edge-path"
                      d={edgePath(getPos(fromNode()!), getPos(toNode()!))}
                    />
                    <text
                      x={(getPos(fromNode()!).x + NODE_W + getPos(toNode()!).x) / 2}
                      y={(getPos(fromNode()!).y + NODE_H / 2 + getPos(toNode()!).y + NODE_H / 2) / 2 - 6}
                      class="edge-label"
                      text-anchor="middle"
                      onClick={() => removeEdge(edge)}
                      style={{ cursor: "pointer" }}
                    >
                      ×
                    </text>
                  </g>
                </Show>
              );
            }}
          </For>
        </svg>

        <For each={canvasNodes()}>
          {(node) => {
            const pos = () => getPos(node);
            const isSelected = () => props.selectedNodeId === node.id;
            const isConnecting = () => connectingFrom()?.nodeId === node.id;

            if (node.type === "ai.agent") {
              return (
                <AgentNodeCard
                  node={node}
                  pos={pos()}
                  nodeWidth={NODE_W}
                  isSelected={isSelected()}
                  isConnecting={isConnecting()}
                  isDragging={draggingId() === node.id}
                  showInputHandle={hasInputPort(props.getNodeMeta?.(node.type), node.type)}
                  onBodyMouseDown={(e) => {
                    if (connectingFrom() && connectingFrom()?.nodeId !== node.id) {
                      onNodeClickForConnect(node.id);
                    } else {
                      onNodeMouseDown(e, node.id);
                    }
                  }}
                  onBodyClick={() => {
                    if (!connectingFrom()) {
                      props.onSelectNode(node.id);
                      props.onOpenNode(node.id);
                    }
                  }}
                  onOutputClick={(e) => onOutputHandleClick(e, node.id)}
                  onDelete={(e) => { e.stopPropagation(); removeNode(node.id); }}
                  onDuplicate={(e) => { e.stopPropagation(); props.onDuplicateNode(node.id); }}
                  onUpdateNode={(updated) => {
                    props.onUpdateGraph({
                      ...props.graph,
                      nodes: props.graph.nodes.map((n) =>
                        n.id === updated.id ? updated : n,
                      ),
                    });
                  }}
                />
              );
            }

            const category = () => node.type.split(".")[0];

            return (
              <div
                class={`canvas-node${isSelected() ? " selected" : ""}${isConnecting() ? " connecting" : ""}`}
                style={{
                  left: `${pos().x}px`,
                  top: `${pos().y}px`,
                  width: `${NODE_W}px`,
                  cursor: draggingId() === node.id ? "grabbing" : "grab",
                }}
                onMouseDown={(e) => {
                  if (connectingFrom() && connectingFrom()?.nodeId !== node.id) {
                    onNodeClickForConnect(node.id);
                  } else {
                    onNodeMouseDown(e, node.id);
                  }
                }}
                onDblClick={(e) => {
                  if (node.type === "chat.trigger") {
                    e.stopPropagation();
                    props.onSelectNode(node.id);
                    props.onOpenChat?.(node.id);
                  }
                }}
                onClick={() => {
                  if (!connectingFrom()) {
                    props.onSelectNode(node.id);
                    if (node.type !== "chat.trigger") {
                      props.onOpenNode(node.id);
                    }
                  }
                }}
              >
                <button
                  class="node-delete-icon"
                  onClick={(e) => { e.stopPropagation(); removeNode(node.id); }}
                  title="Remove node"
                >
                  ×
                </button>
                <button
                  class="node-duplicate-icon"
                  onClick={(e) => { e.stopPropagation(); props.onDuplicateNode(node.id); }}
                  title="Duplicate node"
                  aria-label="Duplicate node"
                >
                  <Copy size={14} strokeWidth={3} />
                </button>

                <div class="node-head">
                  <NodeIcon type={node.type} category={category()} />
                  <strong title={node.type}>
                    {props.getNodeMeta?.(node.type)?.label ??
                      node.type.split(".").pop()?.replace(/_/g, " ")}
                  </strong>
                  <span class="node-status" />
                </div>

                <div class="node-tags">
                  <span>{category()}</span>
                </div>

                <p>{node.type}</p>

                <Show
                  when={node.type === "logic.if"}
                  fallback={
                    <button
                      class="node-handle output"
                      title={isConnecting() ? "Cancel connect" : "Connect to another node"}
                      onClick={(e) => onOutputHandleClick(e, node.id)}
                    >
                      {isConnecting() ? "✕" : "+"}
                    </button>
                  }
                >
                  <button
                    class="node-handle output branch true"
                    title="Connect TRUE branch"
                    onClick={(e) => onOutputHandleClick(e, node.id, "true")}
                  >
                    T
                  </button>
                  <button
                    class="node-handle output branch false"
                    title="Connect FALSE branch"
                    onClick={(e) => onOutputHandleClick(e, node.id, "false")}
                  >
                    F
                  </button>
                </Show>
                <Show when={hasInputPort(props.getNodeMeta?.(node.type), node.type)}>
                  <Show
                    when={node.type === "logic.merge"}
                    fallback={<div class="node-handle input" />}
                  >
                    <div class="node-handle input merge one">1</div>
                    <div class="node-handle input merge two">2</div>
                  </Show>
                </Show>
              </div>
            );
          }}
        </For>
      </div>

      <Show when={connectingFrom()}>
        <div class="canvas-connect-hint">
          Click another node to connect · click canvas to cancel
        </div>
      </Show>
    </div>
  );
}
