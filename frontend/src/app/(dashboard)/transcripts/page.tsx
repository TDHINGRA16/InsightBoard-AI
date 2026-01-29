"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { PageHeader, Loading } from "@/components/common";
import { FileUpload } from "@/components/transcript/FileUpload";
import { DuplicateTranscriptDialog } from "@/components/transcript/DuplicateTranscriptDialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TranscriptStatus } from "@/types";

export default function TranscriptsPage() {
  const router = useRouter();
  const [duplicateId, setDuplicateId] = useState<string | null>(null);
  const [duplicateOpen, setDuplicateOpen] = useState(false);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["transcripts"],
    queryFn: async () => {
      const res = await api.getTranscripts({ page: 1, page_size: 50 });
      return res.data;
    },
    // Auto-refresh list while any transcript is still processing
    refetchInterval: (query) => {
      const list = (query.state.data?.data ?? []) as Array<{ status?: TranscriptStatus }>;
      const hasActive = list.some(
        (t) =>
          t.status === TranscriptStatus.UPLOADED || t.status === TranscriptStatus.ANALYZING
      );
      return hasActive ? 1000 : false;
    },
    refetchIntervalInBackground: true,
  });

  const transcripts = useMemo(() => data?.data ?? [], [data]);

  if (isLoading) return <Loading text="Loading transcripts..." />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Transcripts"
        description="Upload and manage transcripts in the shared workspace."
        actions={
          <Button variant="outline" onClick={() => refetch()}>
            Refresh
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>Upload</CardTitle>
        </CardHeader>
        <CardContent>
          <FileUpload
            onUploadSuccess={(id) => router.push(`/transcripts/${id}/edit`)}
            onDuplicate={(id) => {
              setDuplicateId(id);
              setDuplicateOpen(true);
            }}
          />
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {transcripts.map((t: any) => (
          <Card key={t.id} className="hover:shadow-sm transition-shadow">
            <CardHeader>
              <CardTitle className="text-base truncate">{t.filename}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <Badge variant={t.status === TranscriptStatus.ANALYZED ? "default" : "secondary"}>
                  {t.status}
                </Badge>
                <div className="text-xs text-muted-foreground">{t.task_count ?? 0} tasks</div>
              </div>
              <div className="flex gap-2">
                <Link href={`/transcripts/${t.id}`}>
                  <Button size="sm" variant="outline">
                    View
                  </Button>
                </Link>
                <Link href={`/graph/${t.id}`}>
                  <Button size="sm" disabled={t.status !== TranscriptStatus.ANALYZED}>
                    View Graph
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <DuplicateTranscriptDialog
        transcriptId={duplicateId}
        open={duplicateOpen}
        onOpenChange={setDuplicateOpen}
      />
    </div>
  );
}

