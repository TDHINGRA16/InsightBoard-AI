"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, File, X, AlertCircle, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { api } from "@/lib/api";
import { toast } from "@/lib/toast";
import { cn } from "@/lib/utils";

interface FileUploadProps {
    onUploadSuccess?: (transcriptId: string) => void;
    onUploadError?: (error: string) => void;
    maxSizeMB?: number;
    acceptedTypes?: string[];
}

export function FileUpload({
    onUploadSuccess,
    onUploadError,
    maxSizeMB = 50,
    acceptedTypes = [".txt", ".pdf"],
}: FileUploadProps) {
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    const onDrop = useCallback(
        (acceptedFiles: File[], rejectedFiles: any[]) => {
            setError(null);
            setSuccess(false);

            if (rejectedFiles.length > 0) {
                const rejection = rejectedFiles[0];
                if (rejection.errors[0]?.code === "file-too-large") {
                    setError(`File too large. Maximum size is ${maxSizeMB}MB`);
                } else if (rejection.errors[0]?.code === "file-invalid-type") {
                    setError(`Invalid file type. Accepted: ${acceptedTypes.join(", ")}`);
                } else {
                    setError("File rejected");
                }
                return;
            }

            if (acceptedFiles.length > 0) {
                setFile(acceptedFiles[0]);
            }
        },
        [maxSizeMB, acceptedTypes]
    );

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            "text/plain": [".txt"],
            "application/pdf": [".pdf"],
        },
        maxSize: maxSizeMB * 1024 * 1024,
        multiple: false,
    });

    const handleUpload = async () => {
        if (!file) return;

        setUploading(true);
        setProgress(0);
        setError(null);

        try {
            const formData = new FormData();
            formData.append("file", file);
            formData.append("idempotency_key", `upload-${Date.now()}`);

            // Simulate progress
            const progressInterval = setInterval(() => {
                setProgress((prev) => Math.min(prev + 10, 90));
            }, 200);

            const response = await api.uploadTranscript(formData);

            clearInterval(progressInterval);
            setProgress(100);
            setSuccess(true);

            toast.success("Transcript uploaded successfully!");
            onUploadSuccess?.(response.data.data.id);

            // Reset after success
            setTimeout(() => {
                setFile(null);
                setProgress(0);
                setSuccess(false);
            }, 2000);
        } catch (err: any) {
            const errorMsg = err.response?.data?.detail || "Upload failed";
            setError(errorMsg);
            toast.error(errorMsg);
            onUploadError?.(errorMsg);
        } finally {
            setUploading(false);
        }
    };

    const handleRemove = () => {
        setFile(null);
        setError(null);
        setSuccess(false);
        setProgress(0);
    };

    return (
        <div className="space-y-4">
            {/* Dropzone */}
            <div
                {...getRootProps()}
                className={cn(
                    "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
                    isDragActive
                        ? "border-primary bg-primary/5"
                        : "border-muted-foreground/25 hover:border-primary/50",
                    error && "border-destructive bg-destructive/5",
                    success && "border-green-500 bg-green-500/5"
                )}
            >
                <input {...getInputProps()} />
                <div className="flex flex-col items-center gap-3">
                    {success ? (
                        <CheckCircle className="h-12 w-12 text-green-500" />
                    ) : error ? (
                        <AlertCircle className="h-12 w-12 text-destructive" />
                    ) : (
                        <Upload className="h-12 w-12 text-muted-foreground" />
                    )}

                    {isDragActive ? (
                        <p className="text-primary font-medium">Drop the file here...</p>
                    ) : success ? (
                        <p className="text-green-600 font-medium">Upload successful!</p>
                    ) : error ? (
                        <p className="text-destructive">{error}</p>
                    ) : (
                        <>
                            <p className="font-medium">
                                Drag & drop your transcript file here
                            </p>
                            <p className="text-sm text-muted-foreground">
                                or click to browse. Supports {acceptedTypes.join(", ")} up to{" "}
                                {maxSizeMB}MB
                            </p>
                        </>
                    )}
                </div>
            </div>

            {/* Selected File */}
            {file && !success && (
                <Card className="p-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <File className="h-8 w-8 text-primary" />
                            <div>
                                <p className="font-medium">{file.name}</p>
                                <p className="text-sm text-muted-foreground">
                                    {(file.size / 1024 / 1024).toFixed(2)} MB
                                </p>
                            </div>
                        </div>
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={handleRemove}
                            disabled={uploading}
                        >
                            <X className="h-4 w-4" />
                        </Button>
                    </div>

                    {/* Progress Bar */}
                    {uploading && (
                        <div className="mt-4">
                            <Progress value={progress} className="h-2" />
                            <p className="text-sm text-muted-foreground mt-1">
                                Uploading... {progress}%
                            </p>
                        </div>
                    )}

                    {/* Upload Button */}
                    {!uploading && (
                        <Button onClick={handleUpload} className="w-full mt-4">
                            <Upload className="h-4 w-4 mr-2" />
                            Upload Transcript
                        </Button>
                    )}
                </Card>
            )}
        </div>
    );
}
