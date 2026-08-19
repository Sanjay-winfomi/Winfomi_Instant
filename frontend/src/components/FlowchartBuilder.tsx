"use client";

import { useCallback, useRef, useState } from "react";
import ReactFlow, {
  addEdge,
  Background,
  Handle,
  MarkerType,
  Position,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
  type Connection,
  type Edge,
  type Node,
  type NodeProps,
} from "reactflow";
import "reactflow/dist/style.css";
import "./FlowchartBuilder.css";

type ShapeType = "start" | "process" | "decision";

interface ShapeNodeData {
  label: string;
  shape: ShapeType;
}

const PALETTE: { shape: ShapeType; label: string; hint: string }[] = [
  { shape: "start", label: "Start / End", hint: "Where the flow begins or ends" },
  { shape: "process", label: "Process", hint: "A step or action" },
  { shape: "decision", label: "Decision", hint: "A branching yes/no question" },
];

const SHAPE_TITLE: Record<ShapeType, string> = {
  start: "Start/End",
  process: "Process",
  decision: "Decision",
};

function ShapeNode({ id, data, selected }: NodeProps<ShapeNodeData>) {
  const { setNodes } = useReactFlow();

  const onChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setNodes((nodes) => nodes.map((n) => (n.id === id ? { ...n, data: { ...n.data, label: value } } : n)));
  };

  return (
    <div className={`shape-node shape-node--${data.shape} ${selected ? "is-selected" : ""}`}>
      <Handle type="target" position={Position.Top} />
      <textarea
        className="nodrag shape-node-text"
        value={data.label}
        onChange={onChange}
        placeholder="Describe this step..."
        rows={2}
      />
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

const nodeTypes = { shape: ShapeNode };

function serializeFlowchart(nodes: Node<ShapeNodeData>[], edges: Edge[]): string {
  const sorted = [...nodes].sort((a, b) => a.position.y - b.position.y);
  const indexOf = new Map(sorted.map((n, i) => [n.id, i + 1]));
  const steps = sorted.map(
    (n, i) => `${i + 1}. (${SHAPE_TITLE[n.data.shape]}) ${n.data.label.trim() || "Untitled step"}`
  );
  const flows = edges
    .filter((e) => indexOf.has(e.source) && indexOf.has(e.target))
    .map((e) => `step ${indexOf.get(e.source)} leads to step ${indexOf.get(e.target)}`);

  return [
    "The user manually designed this workflow using a flowchart builder - treat each",
    "numbered step below as part of the process to automate, in the order and",
    "connections given:",
    "",
    "Steps:",
    ...steps,
    "",
    flows.length ? `Flow: ${flows.join(". ")}.` : "",
  ]
    .filter((line) => line !== "")
    .join("\n");
}

interface Props {
  onGenerate: (text: string) => void;
}

let nodeIdCounter = 1;

function Canvas({ onGenerate }: Props) {
  const [nodes, setNodes, onNodesChange] = useNodesState<ShapeNodeData>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const { screenToFlowPosition } = useReactFlow();
  const [error, setError] = useState<string | null>(null);

  const onConnect = useCallback(
    (connection: Connection) =>
      setEdges((eds) =>
        addEdge({ ...connection, animated: false, markerEnd: { type: MarkerType.ArrowClosed, color: "#2fa84e" } }, eds)
      ),
    [setEdges]
  );

  const onDragStart = (event: React.DragEvent, shape: ShapeType) => {
    event.dataTransfer.setData("application/rf-shape", shape);
    event.dataTransfer.effectAllowed = "move";
  };

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const shape = event.dataTransfer.getData("application/rf-shape") as ShapeType;
      if (!shape) return;
      const position = screenToFlowPosition({ x: event.clientX, y: event.clientY });
      const id = `node-${nodeIdCounter++}`;
      setNodes((nds) => nds.concat({ id, type: "shape", position, data: { label: "", shape } }));
    },
    [screenToFlowPosition, setNodes]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const handleGenerate = () => {
    if (nodes.length === 0) {
      setError("Drag at least one shape onto the canvas first.");
      return;
    }
    const emptyLabels = nodes.some((n) => !n.data.label.trim());
    if (emptyLabels) {
      setError("Add text inside every shape before generating.");
      return;
    }
    setError(null);
    onGenerate(serializeFlowchart(nodes, edges));
  };

  return (
    <div className="flowchart-builder">
      <div className="flowchart-palette">
        <span className="flowchart-palette-label">Drag a shape onto the canvas</span>
        {PALETTE.map((item) => (
          <div
            key={item.shape}
            className={`flowchart-palette-item flowchart-palette-item--${item.shape}`}
            draggable
            onDragStart={(e) => onDragStart(e, item.shape)}
          >
            <span className="flowchart-palette-item-label">{item.label}</span>
            <span className="flowchart-palette-item-hint">{item.hint}</span>
          </div>
        ))}
        <p className="flowchart-palette-tip">
          Connect shapes by dragging from one shape&apos;s edge to another. Click inside a shape to edit its text.
          Select a shape or connector and press Delete to remove it.
        </p>
        {error && <p className="flowchart-error">{error}</p>}
        <button type="button" className="btn-primary flowchart-generate" onClick={handleGenerate}>
          Build My AI Demo From This
        </button>
      </div>

      <div className="flowchart-canvas" ref={wrapperRef} onDrop={onDrop} onDragOver={onDragOver}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          deleteKeyCode={["Backspace", "Delete"]}
          fitView
          proOptions={{ hideAttribution: true }}
        >
          <Background gap={18} color="rgba(17,24,39,0.08)" />
        </ReactFlow>
      </div>
    </div>
  );
}

export default function FlowchartBuilder(props: Props) {
  return (
    <ReactFlowProvider>
      <Canvas {...props} />
    </ReactFlowProvider>
  );
}
