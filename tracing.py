import os
import json
import logging
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, asdict, field
from contextlib import contextmanager
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("travel_agent")

# Store traces in memory for display
traces: list["Trace"] = []
current_trace: Optional["Trace"] = None


@dataclass
class Span:
    """A single operation within a trace."""
    span_id: str
    agent: str
    action: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    duration_ms: float = 0
    status: str = "success"
    error: Optional[str] = None
    timestamp: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class Trace:
    """A group of related spans under one trace."""
    trace_id: str
    name: str
    spans: list[Span] = field(default_factory=list)
    start_time: str = ""
    end_time: str = ""
    total_tokens: int = 0
    total_duration_ms: float = 0
    status: str = "running"

    def add_span(self, span: Span):
        self.spans.append(span)
        self.total_tokens += span.total_tokens
        self.total_duration_ms += span.duration_ms

    def complete(self, status: str = "success"):
        self.end_time = datetime.now().isoformat()
        self.status = status

    def to_dict(self):
        return {
            "trace_id": self.trace_id,
            "name": self.name,
            "spans": [s.to_dict() for s in self.spans],
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_tokens": self.total_tokens,
            "total_duration_ms": self.total_duration_ms,
            "status": self.status
        }


@contextmanager
def trace_context(name: str = "travel_agent"):
    """Context manager for grouping spans under a single trace."""
    global current_trace
    trace = Trace(
        trace_id=str(uuid.uuid4())[:8],
        name=name,
        start_time=datetime.now().isoformat()
    )
    current_trace = trace
    traces.append(trace)

    try:
        yield trace
        trace.complete("success")
    except Exception as e:
        trace.complete("error")
        raise
    finally:
        current_trace = None


def log_span(
    agent: str,
    action: str,
    model: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
    duration_ms: float = 0,
    status: str = "success",
    error: Optional[str] = None
) -> Span:
    """Log a span (operation) within the current trace."""
    span = Span(
        span_id=str(uuid.uuid4())[:8],
        agent=agent,
        action=action,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        duration_ms=duration_ms,
        status=status,
        error=error,
        timestamp=datetime.now().isoformat()
    )

    # Add to current trace if one exists
    if current_trace:
        current_trace.add_span(span)

    # Log to console
    trace_name = current_trace.name if current_trace else "no_trace"
    log_msg = (
        f"[{trace_name}:{agent}] {action} | "
        f"Model: {model} | "
        f"Tokens: {prompt_tokens}+{completion_tokens}={total_tokens} | "
        f"Duration: {duration_ms:.0f}ms | "
        f"Status: {status}"
    )

    if error:
        logger.error(f"{log_msg} | Error: {error}")
    else:
        logger.info(log_msg)

    return span


# Alias for backward compatibility
def log_trace(
    agent: str,
    action: str,
    model: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
    duration_ms: float = 0,
    status: str = "success",
    error: Optional[str] = None
):
    """Backward compatible function - logs a span."""
    return log_span(
        agent=agent,
        action=action,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        duration_ms=duration_ms,
        status=status,
        error=error
    )


def get_traces(limit: int = 50) -> list[dict]:
    """Get recent traces."""
    return [t.to_dict() for t in traces[-limit:]]


def get_usage_summary() -> dict:
    """Get summary of token usage."""
    total_prompt = 0
    total_completion = 0
    total_tokens = 0
    total_calls = 0

    by_agent = {}
    by_model = {}

    for trace in traces:
        for span in trace.spans:
            total_prompt += span.prompt_tokens
            total_completion += span.completion_tokens
            total_tokens += span.total_tokens
            total_calls += 1

            if span.agent not in by_agent:
                by_agent[span.agent] = {"calls": 0, "tokens": 0}
            by_agent[span.agent]["calls"] += 1
            by_agent[span.agent]["tokens"] += span.total_tokens

            if span.model not in by_model:
                by_model[span.model] = {"calls": 0, "tokens": 0}
            by_model[span.model]["calls"] += 1
            by_model[span.model]["tokens"] += span.total_tokens

    return {
        "total_traces": len(traces),
        "total_calls": total_calls,
        "total_prompt_tokens": total_prompt,
        "total_completion_tokens": total_completion,
        "total_tokens": total_tokens,
        "by_agent": by_agent,
        "by_model": by_model,
        "estimated_cost_usd": total_tokens * 0.00000015  # gpt-4o-mini pricing approx
    }


def clear_traces():
    """Clear all traces."""
    global traces, current_trace
    traces = []
    current_trace = None


def format_traces_for_display() -> str:
    """Format traces for display in the UI."""
    if not traces:
        return "No traces recorded yet."

    lines = ["## OpenAI Agent Traces\n"]

    summary = get_usage_summary()
    lines.append(f"**Total Traces:** {summary['total_traces']} | **Total Calls:** {summary['total_calls']}")
    lines.append(f"**Total Tokens:** {summary['total_tokens']:,}")
    lines.append(f"**Estimated Cost:** ${summary['estimated_cost_usd']:.4f}\n")

    if summary['by_model']:
        lines.append("**By Model:**")
        for model, data in summary['by_model'].items():
            lines.append(f"  - {model}: {data['calls']} calls, {data['tokens']:,} tokens")
        lines.append("")

    lines.append("---\n")
    lines.append("### Recent Traces\n")

    for trace in reversed(traces[-10:]):
        status_icon = "✓" if trace.status == "success" else "✗"
        lines.append(
            f"**{status_icon} {trace.name}** (ID: {trace.trace_id}) | "
            f"{len(trace.spans)} spans | {trace.total_tokens:,} tokens | "
            f"{trace.total_duration_ms:.0f}ms"
        )

        for span in trace.spans:
            span_status = "✓" if span.status == "success" else "✗"
            lines.append(
                f"  └─ {span_status} `{span.agent}` → {span.action} | "
                f"{span.model} | {span.total_tokens} tokens | {span.duration_ms:.0f}ms"
            )

        lines.append("")

    return "\n".join(lines)
