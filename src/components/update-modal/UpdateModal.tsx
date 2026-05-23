import { Button } from "antd";
import { useUpdateStore } from "@/store/update-store";

export default function UpdateModal() {
  const latestVersion = useUpdateStore((s) => s.latestVersion);
  const changelog = useUpdateStore((s) => s.changelog);
  const isMandatory = useUpdateStore((s) => s.isMandatory);
  const checkModalOpen = useUpdateStore((s) => s.checkModalOpen);
  const closeCheckModal = useUpdateStore((s) => s.closeCheckModal);
  const currentVersion = useUpdateStore((s) => s.currentVersion);

  if (!checkModalOpen) return null;

  const handleUpdate = async () => {
    console.log("[update] update button clicked, calling API:UPDATE:DOWNLOAD");
    if (!window.pywebview) {
      console.error("[update] window.pywebview is not available");
      closeCheckModal();
      return;
    }
    closeCheckModal();

    try {
      const result = (await window.pywebview.api.emit("API:UPDATE:DOWNLOAD", {
        current_version: useUpdateStore.getState().currentVersion,
      })) as any;

      console.log("[update] download result:", JSON.stringify(result));
      if (result?.up_to_date) {
        useUpdateStore.getState().clearUpdate();
      } else if (result?.error) {
        console.log("[update] download error:", result.error);
        useUpdateStore.getState().finishDownload();
      } else {
        console.log("[update] download ok:", result);
      }
    } catch (e) {
      console.log("[update] download exception:", e);
      useUpdateStore.getState().finishDownload();
    }
  };

  return (
    <>
      {/* Backdrop — deep indigo night */}
      <div
        className="fixed inset-0 z-[9990]"
        style={{
          background:
            "radial-gradient(ellipse at 50% 40%, rgba(30,41,59,0.55) 0%, rgba(15,23,42,0.72) 100%)",
          backdropFilter: "blur(4px)",
        }}
        onClick={isMandatory ? undefined : closeCheckModal}
      />

      {/* Card */}
      <div className="fixed inset-0 z-[9991] flex items-center justify-center pointer-events-none">
        <div
          className="pointer-events-auto w-[392px] rounded-3xl overflow-hidden
            bg-[#fcfcfd]
            shadow-[0_0_0_1px_rgba(0,0,0,0.04),0_2px_4px_rgba(0,0,0,0.02),0_24px_64px_rgba(15,23,42,0.18)]
            animate-update-modal-in"
        >
          {/* Top accent — aurora strip */}
          <div
            className="h-[3px]"
            style={{
              background:
                "linear-gradient(90deg, #6366f1 0%, #818cf8 20%, #38bdf8 50%, #a78bfa 80%, #6366f1 100%)",
              backgroundSize: "200% 100%",
              animation: "aurora-shift 4s linear infinite",
            }}
          />

          <div className="px-8 pt-8 pb-7">
            {/* Header */}
            <div className="flex items-start justify-between mb-7">
              <div>
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
                  发现新版本
                </h2>
              </div>
              {!isMandatory && (
                <button
                  onClick={closeCheckModal}
                  className="mt-1 w-8 h-8 flex items-center justify-center rounded-full border-0 outline-none
                    text-[#94a3b8] hover:text-[#475569] hover:bg-[#f1f5f9] cursor-pointer
                    transition-all duration-200"
                >
                  <svg
                    width="14" height="14" viewBox="0 0 24 24"
                    fill="none" stroke="currentColor" strokeWidth="2"
                    strokeLinecap="round"
                  >
                    <path d="M18 6L6 18M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>

            {/* Version showcase */}
            <div className="mb-7">
              <div
                className="relative flex items-center px-1 py-1 rounded-2xl"
                style={{ background: "linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)" }}
              >
                {/* Current — muted, receding */}
                <div className="flex-1 flex flex-col items-center py-3">
                  <span className="text-[10px] font-medium tracking-widest uppercase mb-1 text-[#94a3b8]">
                    当前
                  </span>
                  <span className="text-[28px] font-light tracking-tight text-[#cbd5e1] tabular-nums">
                    {currentVersion}
                  </span>
                </div>

                {/* Divider with arrow */}
                <div className="relative flex-shrink-0">
                  <div className="w-[2px] h-12 bg-[#e2e8f0] rounded-full" />
                  <div
                    className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                      w-7 h-7 rounded-full flex items-center justify-center"
                    style={{
                      background: "linear-gradient(135deg, #6366f1, #818cf8)",
                      boxShadow: "0 2px 8px rgba(99,102,241,0.35)",
                    }}
                  >
                    <svg
                      width="12" height="12" viewBox="0 0 24 24"
                      fill="none" stroke="white" strokeWidth="3"
                      strokeLinecap="round" strokeLinejoin="round"
                    >
                      <path d="M5 12h14M12 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>

                {/* New — prominent, glowing */}
                <div className="flex-1 flex flex-col items-center py-3">
                  <span className="text-[10px] font-medium tracking-widest uppercase mb-1 text-[#6366f1]">
                    最新
                  </span>
                  <span
                    className="text-[28px] font-semibold tracking-tight tabular-nums"
                    style={{
                      color: "#1e293b",
                      textShadow: "0 0 20px rgba(99,102,241,0.2)",
                    }}
                  >
                    {latestVersion}
                  </span>
                </div>
              </div>
            </div>

            {/* Changelog */}
            {changelog && (
              <div className="mb-7">
                <div className="flex items-center gap-2 mb-2.5">
                  <div className="w-1 h-1 rounded-full bg-[#6366f1]" />
                  <span className="text-[10px] font-medium tracking-[0.15em] uppercase text-[#94a3b8]">
                    更新日志
                  </span>
                </div>
                <div
                  className="text-[12px] leading-relaxed rounded-xl px-4 py-3 max-h-24 overflow-y-auto
                    thin-scrollbar"
                  style={{ color: "#64748b", background: "#f8fafc" }}
                >
                  {changelog}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center gap-3">
              <Button
                type="primary"
                onClick={handleUpdate}
                className="flex-1 h-10 rounded-xl font-medium text-[13px] tracking-wide !border-none"
                style={{
                  background: "linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)",
                  boxShadow: "0 2px 8px rgba(99,102,241,0.28), 0 1px 3px rgba(0,0,0,0.06)",
                }}
              >
                立即更新
              </Button>
              {!isMandatory && (
                <Button
                  onClick={closeCheckModal}
                  className="h-10 rounded-xl font-medium text-[13px] tracking-wide
                    !border-[#e2e8f0] !text-[#64748b] hover:!border-[#cbd5e1] hover:!text-[#334155]"
                >
                  暂不更新
                </Button>
              )}
            </div>

            {/* Mandatory warning */}
            {isMandatory && (
              <p className="mt-3.5 text-center text-[11px] tracking-wide" style={{ color: "#f43f5e" }}>
                此版本为强制更新，必须升级后方可继续使用
              </p>
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
