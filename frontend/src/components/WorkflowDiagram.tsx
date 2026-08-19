import { useMemo } from "react";
import ReactFlow, { Background, Handle, Position, type Edge, type Node, type NodeProps } from "reactflow";
import "reactflow/dist/style.css";
import type { StepResult, WorkflowStep } from "../types/api";
import "./WorkflowDiagram.css";

const KIND_MAP: Record<string, string> = {
  READ_DATA: "data",
  SEARCH_DATA: "data",
  WRITE_DATA: "data",
  CLASSIFY: "ai",
  EXTRACT: "ai",
  SUMMARIZE: "ai",
  ANALYZE: "ai",
  GENERATE: "ai",
  CHECK_CONDITION: "decision",
  COMPARE: "logic",
  CALCULATE: "logic",
  MAKE_DECISION: "decision",
  SEND_EMAIL: "action",
  SEND_NOTIFICATION: "action",
  CREATE_TICKET: "action",
  UPDATE_RECORD: "action",
  GENERATE_REPORT: "action",
  ROUTE: "action",
};

interface StepNodeData {
  tool: string;
  kind: string;
  status?: string;
  durationMs?: number;
}

function StepNode({ data }: NodeProps<StepNodeData>) {
  return (
    <div className={`flow-node flow-node--${data.kind} flow-node--${data.status ?? "idle"}`}>
      <Handle type="target" position={Position.Top} />
      <div className="flow-node-label">{data.tool.replaceAll("_", " ")}</div>
      {data.status && (
        <div className="flow-node-status">
          {data.status === "success" && `✓ ${data.durationMs ?? 0}ms`}
          {data.status === "failed" && "✕ failed"}
          {data.status === "blocked" && "blocked"}
        </div>
      )}
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

const nodeTypes = { step: StepNode };

interface Props {
  steps: WorkflowStep[];
  stepResults?: StepResult[];
}

export default function WorkflowDiagram({ steps, stepResults }: Props) {
  const { nodes, edges } = useMemo(() => {
    const nodes: Node[] = steps.map((step, i) => {
      const result = stepResults?.[i];
      return {
        id: `step-${i}`,
        type: "step",
        position: { x: 40, y: i * 96 },
        data: {
          tool: step.tool,
          kind: KIND_MAP[step.tool] ?? "action",
          status: result?.status,
          durationMs: result?.duration_ms,
        },
        draggable: false,
      };
    });

    const edges: Edge[] = steps.slice(1).map((_, i) => ({
      id: `edge-${i}`,
      source: `step-${i}`,
      target: `step-${i + 1}`,
      animated: Boolean(stepResults),
      style: { stroke: "var(--accent-1)" },
    }));

    return { nodes, edges };
  }, [steps, stepResults]);

  const height = Math.max(220, steps.length * 96 + 60);

  return (
    <div className="workflow-diagram" style={{ height }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.25 }}
        proOptions={{ hideAttribution: true }}
        nodesConnectable={false}
        elementsSelectable={false}
        zoomOnScroll={false}
        panOnDrag={false}
      >
        <Background gap={18} color="rgba(255,255,255,0.06)" />
      </ReactFlow>
    </div>
  );
}
