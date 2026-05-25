import { Button } from "antd";
import { LoadingOutlined } from "@ant-design/icons";
import { useState } from "react";
import { useUpdateStore } from "@/store/update-store";

export default function UpdateModal() {
  const latestVersion = useUpdateStore((s) => s.latestVersion);
  const changelog = useUpdateStore((s) => s.changelog);
  const isMandatory = useUpdateStore((s) => s.isMandatory);
  const checkModalOpen = useUpdateStore((s) => s.checkModalOpen);
  const closeCheckModal = useUpdateStore((s) => s.closeCheckModal);
  const currentVersion = useUpdateStore((s) => s.currentVersion);
  const [updating, setUpdating] = useState(false);

  if (!checkModalOpen) return null;

  const handleUpdate = async () => {
    if (!window.pywebview) {
      closeCheckModal();
      return;
    }
    // Show progress modal immediately for instant feedback
    setUpdating(true);
    useUpdateStore.getState().startDownload(0);

    try {
      const result = (await window.pywebview.api.emit("API:UPDATE:DOWNLOAD", {
        current_version: useUpdateStore.getState().currentVersion,
      })) as any;

      if (result?.up_to_date) {
        useUpdateStore.getState().clearUpdate();
        useUpdateStore.getState().cancelDownload();
      } else if (result?.error) {
        useUpdateStore.getState().finishDownload();
      } else if (result?.ok) {
        useUpdateStore.getState().finishDownload();
      }
    } catch {
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

          <div className="px-7 pt-7 pb-6">
            {/* Header */}
            <div className="flex items-start justify-between mb-5">
              <div>
                <p className="text-[10px] font-medium tracking-[0.2em] uppercase mb-1.5 text-[#94a3b8]">
                  时雪 · 创意工坊
                </p>
                <h2 className="flex items-baseline gap-2 text-[20px] font-semibold tracking-tight text-[#1e293b]">
                  发现新版本
                  <span className="inline-flex items-center gap-1.5 text-[13px] font-medium">
                    <span className="text-[#94a3b8]">v{currentVersion}</span>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6366f1" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M5 12h14M12 5l7 7-7 7" />
                    </svg>
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full font-semibold"
                      style={{ background: "linear-gradient(135deg, #eef2ff, #e0e7ff)", color: "#4f46e5" }}>
                      v{latestVersion}
                    </span>
                  </span>
                </h2>
              </div>
              {!isMandatory && (
                <button
                  onClick={closeCheckModal}
                  className="mt-1 w-8 h-8 flex items-center justify-center rounded-full border-0 outline-none
                    text-[#94a3b8] hover:text-[#475569] hover:bg-[#f1f5f9] cursor-pointer
                    transition-all duration-200"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                    <path d="M18 6L6 18M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>

            {/* Changelog — main content */}
            {changelog ? (
              <div className="mb-5">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-1 h-1 rounded-full bg-[#6366f1]" />
                  <span className="text-[11px] font-medium tracking-[0.15em] uppercase text-[#6366f1]">更新内容</span>
                </div>
                <div
                  className="text-[13px] leading-relaxed rounded-xl px-4 py-3.5 max-h-48 overflow-y-auto thin-scrollbar whitespace-pre-wrap"
                  style={{ color: "#334155", background: "#f8fafc", border: "1px solid #f1f5f9" }}
                >
                  {changelog}
                </div>
              </div>
            ) : (
              <p className="text-[13px] text-[#94a3b8] text-center mb-5 py-2">此版本无更新说明</p>
            )}

            {/* Actions */}
            <div className="flex items-center gap-3">
              <Button
                type="primary"
                onClick={handleUpdate}
                disabled={updating}
                icon={updating ? <LoadingOutlined /> : undefined}
                className="flex-1 h-10 rounded-xl font-medium text-[13px] tracking-wide !border-none"
                style={{
                  background: updating ? undefined : "linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)",
                  boxShadow: updating ? undefined : "0 2px 8px rgba(99,102,241,0.28), 0 1px 3px rgba(0,0,0,0.06)",
                }}
              >
                {updating ? "准备中..." : "立即更新"}
              </Button>
              {!isMandatory && (
                <Button
                  onClick={closeCheckModal}
                  disabled={updating}
                  className="h-10 rounded-xl font-medium text-[13px] tracking-wide
                    !border-[#e2e8f0] !text-[#64748b] hover:!border-[#cbd5e1] hover:!text-[#334155]"
                >
                  暂不更新
                </Button>
              )}
            </div>

            {isMandatory && (
              <p className="mt-3.5 text-center text-[11px] tracking-wide text-[#f43f5e]">
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
