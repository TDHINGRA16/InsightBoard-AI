"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

import { api, apiClient } from "@/lib/api";
import { PageHeader, Loading } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/lib/toast";

export default function TranscriptEditPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    const run = async () => {
      try {
        const res = await apiClient.get(`/transcripts/${id}/content`);
        setContent(res.data?.data?.content ?? "");
      } catch {
        toast.error("Failed to load transcript content");
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [id]);

  const save = async () => {
    setSaving(true);
    try {
      const res = await apiClient.put(`/transcripts/${id}`, { content });
      if (res.data?.data?.status === "duplicate_found") {
        toast.info("This content already exists. Redirecting to existing transcript.");
        router.push(`/transcripts/${res.data.data.existing_transcript_id}`);
        return;
      }
      toast.success("Transcript updated");
      setDirty(false);
    } catch (e: any) {
      toast.error(e?.response?.data?.message || "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const startAnalysis = async () => {
    try {
      await api.startAnalysis(id, { force: false });
      toast.success("Analysis started");
      router.push(`/transcripts/${id}`);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Failed to start analysis");
    }
  };

  if (loading) return <Loading text="Loading transcript..." />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Edit Transcript"
        description="Make changes before starting analysis."
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push("/transcripts")}>
              Back
            </Button>
            {dirty && (
              <Button onClick={save} disabled={saving}>
                {saving ? "Saving..." : "Save changes"}
              </Button>
            )}
            <Button variant="secondary" onClick={startAnalysis} disabled={saving}>
              Start analysis
            </Button>
          </div>
        }
      />

      <Card>
        <CardContent className="p-4">
          <Textarea
            value={content}
            onChange={(e) => {
              setContent(e.target.value);
              setDirty(true);
            }}
            rows={22}
            placeholder="Paste or edit transcript content here..."
            className="font-mono"
          />
        </CardContent>
      </Card>
    </div>
  );
}

