import { Button } from "antd";
import { useUpdateStore } from "@/store/update-store";

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatSpeed(bps: number): string {
  if (bps < 1024) return `${bps} B/s`;
  if (bps < 1024 * 1024) return `${(bps / 1024).toFixed(1)} KB/s`;
  return `${(bps / (1024 * 1024)).toFixed(1)} MB/s`;
}

export default function UpdateProgress() {
  const downloading = useUpdateStore((s) => s.downloading);
  const downloadDone = useUpdateStore((s) => s.downloadDone);
  const progress = useUpdateStore((s) => s.progress);
  const currentFile = useUpdateStore((s) => s.currentFile);
  const completedFiles = useUpdateStore((s) => s.completedFiles);
  const totalFiles = useUpdateStore((s) => s.totalFiles);
  const totalBytes = useUpdateStore((s) => s.totalBytes);
  const downloadedBytes = useUpdateStore((s) => s.downloadedBytes);
  const lastSpeed = useUpdateStore((s) => s.lastSpeed);

  if (!downloading && !downloadDone) return null;

  const isPreparing = totalFiles === 0 && !downloadDone;
  const byteProgress = totalBytes > 0 ? Math.round((downloadedBytes / totalBytes) * 100) : 0;

  const handleRestart = () => {
    if (!window.pywebview) return;
    window.pywebview.api.emit("API:UPDATE:APPLY");
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-[9990]"
        style={{
          background:
            "radial-gradient(ellipse at 50% 40%, rgba(30,41,59,0.55) 0%, rgba(15,23,42,0.72) 100%)",
          backdropFilter: "blur(4px)",
        }}
      />

      {/* Card */}
      <div className="fixed inset-0 z-[9991] flex items-center justify-center pointer-events-none">
        <div
          className="pointer-events-auto w-[392px] rounded-3xl overflow-hidden
            bg-[#fcfcfd]
            shadow-[0_0_0_1px_rgba(0,0,0,0.04),0_2px_4px_rgba(0,0,0,0.02),0_24px_64px_rgba(15,23,42,0.18)]
            animate-update-modal-in"
        >
          {/* Aurora strip */}
          <div
            className="h-[3px] transition-all duration-700"
            style={{
              background: downloadDone
                ? "linear-gradient(90deg, #10b981 0%, #34d399 30%, #06b6d4 70%, #10b981 100%)"
                : "linear-gradient(90deg, #6366f1 0%, #818cf8 20%, #38bdf8 50%, #a78bfa 80%, #6366f1 100%)",
              backgroundSize: downloadDone ? "100% 100%" : "200% 100%",
              animation: downloadDone ? "none" : "aurora-shift 4s linear infinite",
            }}
          />

          <div className="px-8 pt-8 pb-7">
            {/* Header */}
            <div className="mb-7">
              <p
                className="text-[10px] font-medium tracking-[0.2em] uppercase mb-2"
                style={{ color: "#94a3b8" }}
              >
                时雪 · 创意工坊
              </p>
              <h2
                className="text-[22px] font-semibold tracking-tight"
                style={{ color: "#1e293b", letterSpacing: "-0.01em" }}
              >
                {downloadDone ? "更新完成" : "正在下载更新"}
              </h2>
            </div>

            {/* Progress area */}
            <div className="flex items-center gap-6 mb-7">
              {/* Ring */}
              <div className="relative w-[76px] h-[76px] flex-shrink-0">
                {isPreparing ? (
                  <div className="w-full h-full flex items-center justify-center">
                    <svg className="animate-spin" width="44" height="44" viewBox="0 0 44 44" fill="none">
                      <circle cx="22" cy="22" r="18" stroke="#f1f5f9" strokeWidth="3" />
                      <circle cx="22" cy="22" r="18" stroke="url(#spinnerGrad)" strokeWidth="3"
                        strokeLinecap="round" strokeDasharray="28 85" />
                      <defs>
                        <linearGradient id="spinnerGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" stopColor="#6366f1" />
                          <stop offset="100%" stopColor="#a78bfa" />
                        </linearGradient>
                      </defs>
                    </svg>
                  </div>
                ) : (
                  <>
                    <svg className="w-full h-full -rotate-90" viewBox="0 0 76 76">
                      <circle cx="38" cy="38" r="32" fill="none" stroke="#f1f5f9" strokeWidth="4" />
                      <circle cx="38" cy="38" r="32" fill="none"
                        stroke={downloadDone ? "#10b981" : "url(#progressGradient)"}
                        strokeWidth="4" strokeLinecap="round"
                        strokeDasharray={`${(progress / 100) * 201} 201`}
                        className="transition-[stroke-dasharray] duration-700 ease-out" />
                      <defs>
                        <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                          <stop offset="0%" stopColor="#6366f1" />
                          <stop offset="100%" stopColor="#818cf8" />
                        </linearGradient>
                      </defs>
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      {downloadDone ? (
                        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#10b981"
                          strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M7 12.5l3.5 3.5L17 9" />
                        </svg>
                      ) : (
                        <span className="text-[16px] font-semibold text-[#1e293b] tabular-nums">{progress}</span>
                      )}
                    </div>
                  </>
                )}
              </div>

              {/* Stats */}
              <div className="flex-1 min-w-0">
                {isPreparing ? (
                  <div>
                    <div className="text-[14px] font-medium text-[#1e293b]">正在准备下载...</div>
                    <div className="text-[11px] text-[#94a3b8] mt-1">正在连接更新服务器</div>
                  </div>
                ) : (
                  <>
                    <div className="text-[13px] font-medium text-[#1e293b] tabular-nums">
                      {completedFiles}
                      <span className="text-[#cbd5e1] mx-1">/</span>
                      {totalFiles}
                      <span className="text-[11px] text-[#94a3b8] ml-1">个文件</span>
                    </div>
                    {totalBytes > 0 && (
                      <div className="text-[12px] font-medium text-[#1e293b] tabular-nums mt-1">
                        {formatSize(downloadedBytes)}
                        <span className="text-[#cbd5e1] mx-1">/</span>
                        {formatSize(totalBytes)}
                        {lastSpeed > 0 && !downloadDone && (
                          <span className="text-[11px] text-[#94a3b8] ml-2">{formatSpeed(lastSpeed)}</span>
                        )}
                      </div>
                    )}
                    {!downloadDone && currentFile && (
                      <div className="text-[11px] text-[#94a3b8] truncate mt-1.5">{currentFile}</div>
                    )}
                    {downloadDone && (
                      <div className="text-[12px] font-medium text-[#10b981] mt-1.5">全部就绪</div>
                    )}
                  </>
                )}
              </div>
            </div>

            {/* Linear bar — byte-based progress */}
            <div className="mb-7 h-1.5 rounded-full bg-[#f1f5f9] overflow-hidden">
              {isPreparing ? (
                <div className="h-full rounded-full animate-pulse"
                  style={{ width: "100%", background: "linear-gradient(90deg, #6366f1, #818cf8, #a78bfa)" }} />
              ) : (
                <div
                  className="h-full rounded-full transition-all duration-700 ease-out"
                  style={{
                    width: `${byteProgress}%`,
                    background: downloadDone
                      ? "linear-gradient(90deg, #10b981, #34d399)"
                      : "linear-gradient(90deg, #6366f1, #818cf8)",
                  }}
                />
              )}
            </div>

            {/* Restart */}
            {downloadDone && (
              <div>
                <Button
                  type="primary"
                  onClick={handleRestart}
                  className="w-full h-10 rounded-xl font-medium text-[13px] tracking-wide !border-none"
                  style={{
                    background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
                    boxShadow: "0 2px 8px rgba(16,185,129,0.28), 0 1px 3px rgba(0,0,0,0.06)",
                  }}
                >
                  立即重启
                </Button>
                <div className="flex items-center gap-2 justify-center mt-3">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#10b981]/40" />
                  <p className="text-[11px] text-[#94a3b8] tracking-wide">
                    所有文件已就绪，重启后生效
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes aurora-shift {
          0%   { background-position: 0% 50%; }
          50%  { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
      `}</style>
    </>
  );
}
