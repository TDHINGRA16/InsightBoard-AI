"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api";
import { toast } from "@/lib/toast";

interface DuplicateTranscriptDialogProps {
  transcriptId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DuplicateTranscriptDialog({
  transcriptId,
  open,
  onOpenChange,
}: DuplicateTranscriptDialogProps) {
  const router = useRouter();
  const [reanalyzing, setReanalyzing] = useState(false);

  const handleView = () => {
    if (!transcriptId) return;
    onOpenChange(false);
    router.push(`/transcripts/${transcriptId}`);
  };

  const handleReanalyze = async () => {
    if (!transcriptId) return;
    setReanalyzing(true);
    try {
      await apiClient.post(`/transcripts/${transcriptId}/re-analyze`);
      toast.success("Re-analysis started");
      onOpenChange(false);
      router.push(`/transcripts/${transcriptId}`);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Failed to start re-analysis");
    } finally {
      setReanalyzing(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Transcript already exists</DialogTitle>
          <DialogDescription>
            This transcript content has already been uploaded. You can view the existing
            transcript (and any existing analysis) or start a re-analysis.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button variant="secondary" onClick={handleView}>
            View existing
          </Button>
          <Button onClick={handleReanalyze} disabled={reanalyzing}>
            {reanalyzing ? "Starting..." : "Re-analyze"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

