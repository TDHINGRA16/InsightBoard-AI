"use client";

import Link from "next/link";
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { PageHeader, Loading } from "@/components/common";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TranscriptStatus } from "@/types";

export default function GraphsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["transcripts-for-graphs"],
    queryFn: async () => {
      const res = await api.getTranscripts({ page: 1, page_size: 100 });
      return res.data;
    },
  });

  const transcripts = useMemo(() => data?.data ?? [], [data]);
  const analyzed = transcripts.filter((t: any) => t.status === TranscriptStatus.ANALYZED);

  if (isLoading) return <Loading text="Loading graphs..." />;

  return (
    <div className="space-y-6">
      <PageHeader title="View Graphs" description="Quick access to analyzed dependency graphs." />

      {analyzed.length === 0 ? (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            No analyzed transcripts yet. Upload a transcript to get started.
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {analyzed.map((t: any) => (
            <Card key={t.id}>
              <CardHeader>
                <CardTitle className="text-base truncate">{t.filename}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="text-xs text-muted-foreground">{t.task_count ?? 0} tasks</div>
                <Link href={`/graph/${t.id}`}>
                  <Button size="sm">View Graph</Button>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

