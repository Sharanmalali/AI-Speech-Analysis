"use client";

import { AnimatePresence, motion } from "framer-motion";
import { FileAudio, Loader2, ShieldCheck, Sparkles, UploadCloud, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import { useDropzone, type FileRejection } from "react-dropzone";
import { toast } from "sonner";

import { PageHeader } from "@/components/dashboard/page-header";
import { Waveform } from "@/components/upload/waveform";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { getErrorMessage } from "@/lib/api";
import { uploadService } from "@/lib/services";
import { cn, formatBytes } from "@/lib/utils";

const ACCEPT = {
  "audio/wav": [".wav"],
  "audio/mpeg": [".mp3"],
  "audio/aac": [".aac"],
  "audio/ogg": [".ogg"],
  "audio/x-m4a": [".m4a"],
  "audio/mp4": [".m4a"],
  "audio/flac": [".flac"],
};
const MAX_BYTES = 100 * 1024 * 1024;
const FORMATS = ["WAV", "MP3", "AAC", "OGG", "M4A", "FLAC"];

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);

  const onDrop = useCallback((accepted: File[], rejections: FileRejection[]) => {
    if (rejections.length > 0) {
      toast.error(rejections[0].errors[0]?.message ?? "File rejected");
      return;
    }
    if (accepted[0]) setFile(accepted[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPT,
    maxSize: MAX_BYTES,
    multiple: false,
    disabled: uploading,
  });

  async function startUpload() {
    if (!file) return;
    setUploading(true);
    setProgress(0);
    try {
      const res = await uploadService.upload(file, setProgress);
      toast.success("Upload complete — analysis queued");
      router.push(`/dashboard/processing/${res.job_id}`);
    } catch (error) {
      toast.error(getErrorMessage(error));
      setUploading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <PageHeader
        eyebrow="New analysis"
        title="Upload a conversation"
        description="Drop in a multi-speaker recording and we'll diarize, transcribe and screen it end to end."
      />

      <AnimatePresence mode="wait">
        {!file ? (
          <motion.div
            key="dropzone"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.3 }}
          >
            <div
              {...getRootProps()}
              className={cn(
                "group relative flex cursor-pointer flex-col items-center justify-center overflow-hidden rounded-[2rem] border-2 border-dashed p-14 text-center transition-all duration-300",
                isDragActive
                  ? "border-primary bg-primary/[0.06] scale-[1.01]"
                  : "border-border bg-card/40 hover:border-primary/50 hover:bg-secondary/40",
              )}
            >
              <input {...getInputProps()} />
              {isDragActive && <div className="absolute inset-0 aurora opacity-30" />}
              <motion.div
                animate={{ y: isDragActive ? -8 : 0, scale: isDragActive ? 1.05 : 1 }}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
                className="relative mb-5 flex h-20 w-20 items-center justify-center rounded-3xl bg-gradient-to-br from-primary to-accent text-white shadow-glow"
              >
                <UploadCloud className="h-9 w-9" />
              </motion.div>
              <p className="relative font-display text-xl font-semibold">
                {isDragActive ? "Drop to upload" : "Drag & drop your audio"}
              </p>
              <p className="relative mt-1 text-sm text-muted-foreground">
                or <span className="font-medium text-primary">browse files</span> · up to 100 MB
              </p>
              <div className="relative mt-6 flex flex-wrap items-center justify-center gap-2">
                {FORMATS.map((f) => (
                  <span
                    key={f}
                    className="rounded-lg border border-border/60 bg-background/60 px-2.5 py-1 text-[11px] font-semibold text-muted-foreground"
                  >
                    {f}
                  </span>
                ))}
              </div>
            </div>

            <div className="mt-4 flex items-center justify-center gap-2 text-xs text-muted-foreground">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
              Files are validated and encrypted in transit.
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="selected"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.3 }}
            className="panel space-y-5 p-6"
          >
            <div className="flex items-center justify-between gap-4">
              <div className="flex min-w-0 items-center gap-3">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/15 to-accent/15 text-primary">
                  <FileAudio className="h-5 w-5" />
                </div>
                <div className="min-w-0">
                  <p className="truncate font-semibold">{file.name}</p>
                  <p className="text-xs text-muted-foreground">{formatBytes(file.size)}</p>
                </div>
              </div>
              {!uploading && (
                <Button size="icon" variant="ghost" onClick={() => setFile(null)} aria-label="Remove file">
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>

            <Waveform file={file} />

            {uploading && (
              <div className="space-y-2">
                <Progress value={progress} />
                <p className="text-right text-xs tabular-nums text-muted-foreground">{progress}%</p>
              </div>
            )}

            <Button onClick={startUpload} variant="gradient" size="lg" className="w-full" disabled={uploading}>
              {uploading ? (
                <><Loader2 className="h-4 w-4 animate-spin" /> Uploading…</>
              ) : (
                <><Sparkles className="h-4 w-4" /> Analyse recording</>
              )}
            </Button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
