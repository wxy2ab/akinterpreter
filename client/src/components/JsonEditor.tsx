import React, { useEffect, useState, useMemo, useCallback } from 'react';
import Editor from '@monaco-editor/react';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  BackgroundVariant,
  NodeProps,
  useNodesState,
  useEdgesState,
  MarkerType,
  useReactFlow,
  ReactFlowProvider,
  applyNodeChanges,
  applyEdgeChanges,
  NodeChange,
  EdgeChange,
  Connection,
  addEdge
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Code, GitBranch } from 'lucide-react';

interface JsonEditorProps {
  initialJson: any;
  onJsonChange: (updatedJson: any) => void;
}

const NODE_WIDTH = 300;
const NODE_HEIGHT = 250; // Increased height to accommodate content without scrollbar
const NODE_VERTICAL_SPACING = 100; // Adjusted spacing
const QUERY_SUMMARY_SPACING = 50;

const CustomNode: React.FC<NodeProps> = ({ data }) => {
  return (
    <div className="px-4 py-2 shadow-md rounded-md bg-gray-800 border-2 border-gray-600 text-white w-[300px]">
      <div className="text-lg font-bold">{data.title}</div>
      <hr className="my-2 border-gray-600" />
      <div className="text-sm">
        {Object.entries(data.content).map(([key, value], index, array) => {
          if (key === 'selected_functions' || key === 'library') return null;
          if ((key === 'required_data' || key === 'save_data_to') && Array.isArray(value) && value.length === 0) return null;
          return (
            <React.Fragment key={key}>
              <div>
                <strong>{key}:</strong> 
                {Array.isArray(value) ? value.join(', ') : String(value)}
              </div>
              {index < array.length - 1 && <hr className="my-2 border-gray-600" />}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

const nodeTypes = {
  custom: CustomNode,
};

const getLayoutedElements = (nodes: Node[], edges: Edge[]) => {
  const layoutedNodes = nodes.map((node, index) => {
    let yPosition;
    if (node.id === 'query_summary') {
      yPosition = 0;
    } else if (node.id === '1') {
      yPosition = QUERY_SUMMARY_SPACING + NODE_HEIGHT;
    } else {
      yPosition = QUERY_SUMMARY_SPACING + (parseInt(node.id) - 1) * (NODE_HEIGHT + NODE_VERTICAL_SPACING) + NODE_HEIGHT;
    }
    return {
      ...node,
      position: { x: 0, y: yPosition }
    };
  });

  return { nodes: layoutedNodes, edges };
};

const FlowChart: React.FC<{ initialNodes: Node[], initialEdges: Edge[] }> = ({ initialNodes, initialEdges }) => {
  const { fitView } = useReactFlow();
  const [nodes, setNodes] = useState<Node[]>(initialNodes);
  const [edges, setEdges] = useState<Edge[]>(initialEdges);
  const [initialFit, setInitialFit] = useState<boolean>(true);

  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges]);

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds)),
    [setNodes]
  );
  
  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    [setEdges]
  );

  const onConnect = useCallback(
    (connection: Connection) => setEdges((eds) => addEdge(connection, eds)),
    [setEdges]
  );

  useEffect(() => {
    if (initialFit) {
      fitView({ padding: 0.2 });
      setInitialFit(false);
    }
  }, [fitView, initialFit]);

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={onConnect}
      nodeTypes={nodeTypes}
      fitView
      minZoom={0.1}
      maxZoom={1.5}
      nodesDraggable={true}
      zoomOnScroll={true}
      panOnScroll={true}
      elementsSelectable={true}
    >
      <Controls />
      <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
    </ReactFlow>
  );
};

const JsonEditor: React.FC<JsonEditorProps> = ({ initialJson, onJsonChange }) => {
  const [value, setValue] = useState<string>(JSON.stringify(initialJson, null, 2));
  const [view, setView] = useState<'flowchart' | 'json'>('flowchart');

  useEffect(() => {
    setValue(JSON.stringify(initialJson, null, 2));
  }, [initialJson]);

  const handleEditorChange = (value: string | undefined) => {
    if (value === undefined) return;
    setValue(value);
    try {
      const parsedJson = JSON.parse(value);
      onJsonChange(parsedJson);
    } catch (error) {
      console.error('Invalid JSON detected:', error);
    }
  };

  const handleViewChange = (value: string) => {
    setView(value as 'json' | 'flowchart');
  };

  const flowElements = useMemo(() => {
    if (view !== 'flowchart') return { nodes: [], edges: [] };

    try {
      const data = JSON.parse(value);
      let nodes: Node[] = [];
      const edges: Edge[] = [];

      // Add query summary node
      nodes.push({
        id: 'query_summary',
        type: 'custom',
        data: { 
          title: 'Query Summary',
          content: { summary: data.query_summary }
        },
        position: { x: 0, y: 0 },
        draggable: true,
      });

      if (data.steps && typeof data.steps === 'object') {
        const stepNumbers = Object.keys(data.steps).sort((a, b) => parseInt(a) - parseInt(b));
        
        stepNumbers.forEach((stepNumber, index) => {
          const step = data.steps[stepNumber];
          nodes.push({
            id: `${step.step_number}`,
            type: 'custom',
            data: { 
              title: `Step ${step.step_number}`,
              content: step
            },
            position: { x: 0, y: 0 },
            draggable: true,
          });

          if (index === 0) {
            edges.push({
              id: `e-summary-${step.step_number}`,
              source: 'query_summary',
              target: `${step.step_number}`,
              animated: true,
              type: 'smoothstep',
              markerEnd: {
                type: MarkerType.ArrowClosed,
              },
            });
          } else {
            edges.push({
              id: `e${stepNumbers[index-1]}-${step.step_number}`,
              source: `${stepNumbers[index-1]}`,
              target: `${step.step_number}`,
              animated: true,
              type: 'smoothstep',
              markerEnd: {
                type: MarkerType.ArrowClosed,
              },
            });
          }
        });

        // Add summary node
        nodes.push({
          id: 'summary',
          type: 'custom',
          data: { 
            title: '分析总结',
            content: { summary: '基于以上步骤的分析总结' }
          },
          position: { x: 0, y: 0 },
          draggable: true,
        });

        edges.push({
          id: `e-last-summary`,
          source: `${stepNumbers[stepNumbers.length - 1]}`,
          target: 'summary',
          animated: true,
          type: 'smoothstep',
          markerEnd: {
            type: MarkerType.ArrowClosed,
          },
        });
      }

      return getLayoutedElements(nodes, edges);
    } catch (error) {
      console.error('Error parsing JSON:', error);
      return { nodes: [], edges: [] };
    }
  }, [value, view]);

  return (
    <div className="h-full w-full flex flex-col">
      <div className="flex justify-end">
        <ToggleGroup type="single" value={view} onValueChange={handleViewChange} className="border-0">
          <ToggleGroupItem value="flowchart" aria-label="View as flowchart">
            <GitBranch className="h-4 w-4" />
          </ToggleGroupItem>
          <ToggleGroupItem value="json" aria-label="View as JSON">
            <Code className="h-4 w-4" />
          </ToggleGroupItem>
        </ToggleGroup>
      </div>
      <div className="flex-grow overflow-auto">
        {view === 'json' ? (
          <Editor
            height="100%"
            defaultLanguage="json"
            defaultValue={value}
            value={value}
            onChange={handleEditorChange}
            theme="vs-dark"
            options={{
              automaticLayout: true,
              wordWrap: 'on',
              formatOnType: true,
            }}
          />
        ) : (
          <ReactFlowProvider>
            <FlowChart initialNodes={flowElements.nodes} initialEdges={flowElements.edges} />
          </ReactFlowProvider>
        )}
      </div>
    </div>
  );
};

export default JsonEditor;
