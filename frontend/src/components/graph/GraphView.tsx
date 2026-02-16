import { useEffect, useRef, useState, useCallback } from "react";
import * as d3 from "d3";
import type { GraphData, GraphNode, GraphLink } from "../../types";
import { getFullGraph, getNeighborhood } from "../../api/graph";

interface GraphViewProps {
  focusPageId?: string;
  onOpenPage: (pageId: string, title: string) => void;
}

interface SimNode extends d3.SimulationNodeDatum {
  id: string;
  title: string;
  workspace: string;
  tags: string[];
  link_count: number;
}

interface SimLink extends d3.SimulationLinkDatum<SimNode> {
  source: SimNode | string;
  target: SimNode | string;
}

export function GraphView({ focusPageId, onOpenPage }: GraphViewProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [nodeCount, setNodeCount] = useState(0);
  const [linkCount, setLinkCount] = useState(0);

  const loadGraph = useCallback(async () => {
    setLoading(true);
    try {
      const data = focusPageId
        ? await getNeighborhood(focusPageId)
        : await getFullGraph();
      setGraphData(data);
      setNodeCount(data.nodes.length);
      setLinkCount(data.links.length);
    } catch {
      setGraphData({ nodes: [], links: [] });
    } finally {
      setLoading(false);
    }
  }, [focusPageId]);

  useEffect(() => {
    loadGraph();
  }, [loadGraph]);

  useEffect(() => {
    if (!graphData || !svgRef.current || !containerRef.current) return;
    if (graphData.nodes.length === 0) return;

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Clear previous
    d3.select(svgRef.current).selectAll("*").remove();

    const svg = d3
      .select(svgRef.current)
      .attr("width", width)
      .attr("height", height);

    // Create container group for zoom
    const g = svg.append("g");

    // Zoom behavior
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on("zoom", (event: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
        g.attr("transform", event.transform.toString());
      });

    svg.call(zoom);

    // Prepare data
    const nodes: SimNode[] = graphData.nodes.map((n: GraphNode) => ({
      ...n,
      x: undefined,
      y: undefined,
    }));

    const nodeMap = new Map(nodes.map((n) => [n.id, n]));

    const links: SimLink[] = graphData.links
      .filter(
        (l: GraphLink) => nodeMap.has(l.source) && nodeMap.has(l.target),
      )
      .map((l: GraphLink) => ({
        source: l.source,
        target: l.target,
      }));

    // Color scale by workspace — muted dark-friendly palette
    const workspaces = Array.from(new Set(nodes.map((n) => n.workspace)));
    const colorScale = d3
      .scaleOrdinal<string>()
      .domain(workspaces)
      .range([
        "#7c7cf5",
        "#d06d98",
        "#2ea89a",
        "#c9952e",
        "#9b7ce0",
        "#2ba5bf",
        "#d07a3a",
        "#7db836",
      ]);

    // Simulation
    const simulation = d3
      .forceSimulation<SimNode>(nodes)
      .force(
        "link",
        d3
          .forceLink<SimNode, SimLink>(links)
          .id((d) => d.id)
          .distance(80),
      )
      .force("charge", d3.forceManyBody().strength(-200))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(30));

    // Links
    const link = g
      .append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", "#3a3a3a")
      .attr("stroke-width", 1)
      .attr("stroke-opacity", 0.6);

    // Nodes
    const node = g
      .append("g")
      .selectAll<SVGCircleElement, SimNode>("circle")
      .data(nodes)
      .join("circle")
      .attr("r", (d) => Math.max(5, Math.min(15, 4 + d.link_count * 2)))
      .attr("fill", (d) => colorScale(d.workspace))
      .attr("stroke", "#2e2e2e")
      .attr("stroke-width", 1.5)
      .attr("cursor", "pointer")
      .on("click", (_event, d) => {
        onOpenPage(d.id, d.title);
      })
      .on("mouseenter", (_event, d) => {
        setHoveredNode(d.id);
        d3.select(_event.currentTarget as Element)
          .transition()
          .duration(150)
          .attr(
            "r",
            Math.max(7, Math.min(18, 4 + d.link_count * 2 + 3)),
          )
          .attr("stroke-width", 2.5);
      })
      .on("mouseleave", (_event, d) => {
        setHoveredNode(null);
        d3.select(_event.currentTarget as Element)
          .transition()
          .duration(150)
          .attr("r", Math.max(5, Math.min(15, 4 + d.link_count * 2)))
          .attr("stroke-width", 1.5);
      })
      .call(
        d3
          .drag<SVGCircleElement, SimNode>()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          }),
      );

    // Labels
    const label = g
      .append("g")
      .selectAll<SVGTextElement, SimNode>("text")
      .data(nodes)
      .join("text")
      .attr("class", "graph-label")
      .attr("text-anchor", "middle")
      .attr("fill", "#9b9b9b")
      .attr("font-size", "11px")
      .attr("dy", (d) =>
        Math.max(5, Math.min(15, 4 + d.link_count * 2)) + 14 + "px",
      )
      .text((d) =>
        d.title.length > 20 ? d.title.substring(0, 18) + "..." : d.title,
      );

    // Tick
    simulation.on("tick", () => {
      link
        .attr("x1", (d) => (d.source as SimNode).x ?? 0)
        .attr("y1", (d) => (d.source as SimNode).y ?? 0)
        .attr("x2", (d) => (d.target as SimNode).x ?? 0)
        .attr("y2", (d) => (d.target as SimNode).y ?? 0);

      node.attr("cx", (d) => d.x ?? 0).attr("cy", (d) => d.y ?? 0);

      label.attr("x", (d) => d.x ?? 0).attr("y", (d) => d.y ?? 0);
    });

    // Highlight focused node
    if (focusPageId) {
      node
        .filter((d) => d.id === focusPageId)
        .attr("stroke", "#f59e0b")
        .attr("stroke-width", 3);
    }

    return () => {
      simulation.stop();
    };
  }, [graphData, focusPageId, onOpenPage]);

  // Handle resize
  useEffect(() => {
    const handleResize = () => {
      if (graphData && graphData.nodes.length > 0) {
        // Trigger re-render
        setGraphData({ ...graphData });
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [graphData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-content">
        <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-content">
      {/* Header */}
      <div className="px-6 pt-6 pb-3 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-content-text">Knowledge Graph</h1>
          <p className="text-xs text-content-muted mt-0.5">
            {nodeCount} nodes &middot; {linkCount} connections
            {focusPageId && " (neighborhood view)"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {focusPageId && (
            <button
              onClick={() => loadGraph()}
              className="px-3 py-1.5 text-xs text-content-muted hover:text-content-text border border-content-border rounded-md hover:bg-content-tertiary transition-colors"
            >
              Show Full Graph
            </button>
          )}
          <button
            onClick={loadGraph}
            className="px-3 py-1.5 text-xs text-content-muted hover:text-content-text border border-content-border rounded-md hover:bg-content-tertiary transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Tooltip */}
      {hoveredNode && graphData && (
        <div className="absolute top-20 right-6 bg-content-secondary border border-content-border rounded-lg shadow-lg p-3 z-10 max-w-xs animate-fade-in">
          {(() => {
            const n = graphData.nodes.find((node) => node.id === hoveredNode);
            if (!n) return null;
            return (
              <>
                <div className="text-sm font-medium text-content-text">
                  {n.title}
                </div>
                <div className="text-xs text-content-muted mt-0.5">
                  {n.workspace} &middot; {n.link_count} links
                </div>
                {n.tags.length > 0 && (
                  <div className="flex gap-1 mt-1 flex-wrap">
                    {n.tags.map((tag) => (
                      <span
                        key={tag}
                        className="text-[10px] px-1.5 py-0.5 rounded-full bg-accent/10 text-accent-light"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </>
            );
          })()}
        </div>
      )}

      {/* Graph */}
      <div ref={containerRef} className="flex-1 overflow-hidden relative">
        {graphData && graphData.nodes.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-4xl mb-3 opacity-30">{"\u25C8"}</div>
              <p className="text-content-muted text-sm">
                No pages with links yet.
              </p>
              <p className="text-content-faint text-xs mt-1">
                Create pages with [[wiki links]] to build your graph.
              </p>
            </div>
          </div>
        ) : (
          <svg
            ref={svgRef}
            className="w-full h-full"
            style={{ background: "#191919" }}
          />
        )}
      </div>
    </div>
  );
}
