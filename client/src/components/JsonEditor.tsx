import React, { useEffect, useState, useMemo, useCallback } from 'react';
import Editor from '@monaco-editor/react';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import ReactFlow, { Node, Edge, Controls, Background, NodeProps, useNodesState, useEdgesState, MarkerType, useReactFlow, ReactFlowProvider } from 'reactflow';
import 'reactflow/dist/style.css';
import { Code, GitBranch } from 'lucide-react';

interface JsonEditorProps {
  initialJson: any;
  onJsonChange: (updatedJson: any) => void;
}

const NODE_WIDTH = 300;
const NODE_HEIGHT = 200;
const NODE_VERTICAL_SPACING = 150;
const QUERY_SUMMARY_SPACING = 50; // Reduced spacing for query_summary node

const CustomNode: React.FC<NodeProps> = ({ data }) => {
  return (
    <div className="px-4 py-2 shadow-md rounded-md bg-gray-800 border-2 border-gray-600 text-white w-[300px]">
      <div className="text-lg font-bold">{data.title}</div>
      <hr className="my-2 border-gray-600" />
      <div dangerouslySetInnerHTML={{ __html: data.content }} className="text-sm" />
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
      yPosition = QUERY_SUMMARY_SPACING + (index - 1) * (NODE_HEIGHT + NODE_VERTICAL_SPACING) + NODE_HEIGHT;
    }
    return {
      ...node,
      position: { x: 0, y: yPosition }
    };
  });

  return { nodes: layoutedNodes, edges };
};

const FlowChart: React.FC<{ nodes: Node[], edges: Edge[] }> = ({ nodes, edges }) => {
  const { fitView } = useReactFlow();
  const [localNodes, setLocalNodes, onNodesChange] = useNodesState(nodes);
  const [localEdges, setLocalEdges, onEdgesChange] = useEdgesState(edges);

  useEffect(() => {
    setLocalNodes(nodes);
    setLocalEdges(edges);
  }, [nodes, edges, setLocalNodes, setLocalEdges]);

  useEffect(() => {
    fitView({ padding: 0.2 });
  }, [fitView, localNodes, localEdges]);

  return (
    <ReactFlow
      nodes={localNodes}
      edges={localEdges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      nodeTypes={nodeTypes}
      fitView
      minZoom={0.1}
      maxZoom={1.5}
    >
      <Controls />
      <Background />
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
          content: `<p>${data.query_summary}</p>`
        },
        position: { x: 0, y: 0 },
      });

      if (Array.isArray(data.steps)) {
        data.steps.forEach((step: any, index: number) => {
          const stepContent = Object.entries(step)
            .map(([key, value]) => `
              <div>
                <strong>${key}:</strong> 
                ${Array.isArray(value) ? value.join(', ') : value}
              </div>
            `)
            .join('<hr class="my-2 border-gray-600" />');

          nodes.push({
            id: `${step.step_number}`,
            type: 'custom',
            data: { 
              title: `Step ${step.step_number}`,
              content: stepContent
            },
            position: { x: 0, y: 0 },
          });

          if (index === 0) {
            edges.push({
              id: `e-summary-${index + 1}`,
              source: 'query_summary',
              target: `${index + 1}`,
              animated: true,
              type: 'smoothstep',
              markerEnd: {
                type: MarkerType.ArrowClosed,
              },
            });
          } else {
            edges.push({
              id: `e${index}-${index + 1}`,
              source: `${index}`,
              target: `${index + 1}`,
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
            content: '<p>基于以上步骤的分析总结</p>'
          },
          position: { x: 0, y: 0 },
        });

        edges.push({
          id: `e-last-summary`,
          source: `${data.steps.length}`,
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
            <FlowChart nodes={flowElements.nodes} edges={flowElements.edges} />
          </ReactFlowProvider>
        )}
      </div>
    </div>
  );
};

export default JsonEditor;