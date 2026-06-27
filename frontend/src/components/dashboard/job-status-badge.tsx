import { Badge } from "@/components/ui/badge";
import type { JobStatus } from "@/lib/types";
import { titleCase } from "@/lib/utils";

const MAP: Record<JobStatus, "default" | "success" | "warning" | "destructive" | "secondary"> = {
  pending: "secondary",
  queued: "secondary",
  processing: "warning",
  completed: "success",
  failed: "destructive",
  cancelled: "secondary",
};

export function JobStatusBadge({ status }: { status: JobStatus }) {
  return <Badge variant={MAP[status]}>{titleCase(status)}</Badge>;
}
