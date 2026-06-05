import { useState, useEffect, useRef, type FC } from "react";
import { Button, Input, Modal, Popconfirm, Tooltip, message, Spin, Radio } from "antd";
import {
  PlusOutlined, DeleteOutlined, PlayCircleOutlined,
  ReloadOutlined, UserOutlined, ScanOutlined, ThunderboltOutlined,
  FolderOpenOutlined,
} from "@ant-design/icons";
import { useAccountStore } from "@/store/account-store";

const TYPE_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  qr:       { label: "官服", color: "#1677ff", bg: "rgba(22,119,255,0.08)" },
  vivo:     { label: "Vivo", color: "#722ed1", bg: "rgba(114,46,209,0.08)" },
  bilibili: { label: "B站",  color: "#13c2c2", bg: "rgba(19,194,194,0.08)" },
  huawei:   { label: "华为", color: "#fa8c16", bg: "rgba(250,140,22,0.08)" },
};

function getTypeInfo(t?: string) {
  return TYPE_CONFIG[t ?? "qr"] ?? TYPE_CONFIG.qr;
}

const AccountsPage: FC = () => {
  const accounts = useAccountStore((s) => s.accounts);
  const loading = useAccountStore((s) => s.loading);
  const loadAccounts = useAccountStore((s) => s.loadAccounts);
  const [dragIdx, setDragIdx] = useState<number | null>(null);
  const [overIdx, setOverIdx] = useState<number | null>(null);

  useEffect(() => { loadAccounts(); }, [loadAccounts]);

  const handleDragStart = (i: number) => setDragIdx(i);
  const handleDragEnd = () => { setDragIdx(null); setOverIdx(null); };

  const handleDragOver = (e: React.DragEvent, i: number) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    if (dragIdx !== null && dragIdx !== i) setOverIdx(i);
  };

  const handleDrop = async (e: React.DragEvent, i: number) => {
    e.preventDefault();
    if (dragIdx === null || dragIdx === i) return;
    const reordered = [...accounts];
    const [moved] = reordered.splice(dragIdx, 1);
    reordered.splice(i, 0, moved);
    setDragIdx(null);
    setOverIdx(null);
    await window.pywebview?.api.emit("API:ACCOUNT:SAVE_ORDER", reordered.map(a => a.name));
    loadAccounts();
  };

  // ---- 游戏路径 ----
  const [gamePath, setGamePath] = useState<string>("");
  const [loadingGamePath, setLoadingGamePath] = useState(false);

  const loadGamePath = async () => {
    try {
      const p = await window.pywebview?.api.emit("API:GAME:GET_PATH") as any;
      setGamePath(String(p ?? ""));
    } catch { /* */ }
  };

  useEffect(() => { loadGamePath(); }, []);

  const handleChangeGamePath = async () => {
    setLoadingGamePath(true);
    try {
      const result = await window.pywebview?.api.emit("API:GAME:SET_PATH") as any;
      if (result?.success) {
        setGamePath(result.path);
        message.success("游戏路径已更新");
      } else if (!result?.cancelled) {
        message.error(result?.error ?? "设置失败");
      }
    } catch { message.error("设置失败"); }
    setLoadingGamePath(false);
  };

  // ---- 录制 ----
  const [recordModalOpen, setRecordModalOpen] = useState(false);
  const [recordName, setRecordName] = useState("");
  const [recordMode, setRecordMode] = useState<"qr" | "vivo" | "bilibili" | "huawei">("qr");
  const [recording, setRecording] = useState(false);
  const [recordStatus, setRecordStatus] = useState<string>("");

  const startRecording = async () => {
    if (!recordName.trim()) return;
    setRecording(true);
    setRecordStatus("启动代理中...");
    try {
      if (recordMode === "vivo" || recordMode === "bilibili" || recordMode === "huawei") {
        await window.pywebview?.api.emit("API:ACCOUNT:RECORD:START:CHANNEL", recordName.trim(), recordMode);
        const labels: Record<string, string> = { vivo: "Vivo", bilibili: "B站", huawei: "华为" };
        setRecordStatus(`请在弹出窗口中登录${labels[recordMode]}账号，然后在游戏中点击扫码登录`);
      } else {
        await window.pywebview?.api.emit("API:ACCOUNT:RECORD:START", recordName.trim());
        setRecordStatus(`正在录制 — 请在游戏中手动登录账号「${recordName.trim()}」`);
      }
    } catch {
      setRecordStatus("启动失败");
      setRecording(false);
    }
  };

  const stopRecording = async () => {
    try {
      const result = await window.pywebview?.api.emit("API:ACCOUNT:RECORD:STOP", recordName.trim());
      if (result?.account) {
        message.success(`账号「${result.account}」已保存`);
        loadAccounts();
      } else if (result?.error) {
        message.error(result.error);
      }
    } catch { /* */ }
    setRecording(false);
    setRecordModalOpen(false);
    setRecordName("");
  };

  const closeRecord = () => {
    if (recording) {
      stopRecording();
    } else {
      setRecordModalOpen(false);
      setRecordName("");
      setRecordMode("qr");
    }
  };

  // ---- 回放 ----
  const [replaying, setReplaying] = useState<string>("");

  const handleReplay = async (name: string) => {
    setReplaying(name);
    try {
      await window.pywebview?.api.emit("API:ACCOUNT:REPLAY:START", name);
      message.info(`正在回放「${name}」——请在游戏中触发登录`);
    } catch { setReplaying(""); }
  };

  // ---- 一键启动 ----
  const [quickStarting, setQuickStarting] = useState<string>("");

  const handleQuickStart = async (name: string) => {
    setQuickStarting(name);
    try {
      await window.pywebview?.api.emit("API:ACCOUNT:QUICK_START", name);
      message.success(`「${name}」一键启动完成`);
    } catch { message.error("一键启动失败"); }
    setQuickStarting("");
  };

  const stopReplay = async () => {
    try {
      await window.pywebview?.api.emit("API:ACCOUNT:REPLAY:STOP");
    } catch { /* */ }
    setReplaying("");
  };

  // ---- 轮询自动结束 ----
  const pollRef = useRef<ReturnType<typeof setInterval>>(undefined);

  useEffect(() => {
    if (recording || replaying) {
      pollRef.current = setInterval(async () => {
        const status = await window.pywebview?.api.emit("API:ACCOUNT:RECORD:STATUS");
        if (status?.status === "done") {
          if (recording) stopRecording();
          if (replaying) stopReplay();
        }
      }, 2000);
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [recording, replaying]);

  // ---- 删除 ----
  const handleDelete = async (name: string) => {
    try {
      await window.pywebview?.api.emit("API:ACCOUNT:DELETE", name);
      message.success("已删除");
      loadAccounts();
    } catch { /* */ }
  };

  return (
    <div className="page-container">
      {/* ── Header ── */}
      <div className="page-header">
        <div className="page-header__left">
          <span className="page-header__accent" />
          <h2 className="page-header__title">
            <UserOutlined className="mr-2 text-[#1677ff]" />
            账号管理
          </h2>
          <span className="page-header__badge">
            {accounts.length} 个账号
          </span>
        </div>
        <div className="flex items-center gap-2">
          {replaying && (
            <Button danger size="small" onClick={stopReplay}>
              停止回放
            </Button>
          )}
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setRecordModalOpen(true)}>
            录入账号
          </Button>
        </div>
      </div>

      {/* ── Game path toolbar ── */}
      <div
        className="flex items-center gap-2 shrink-0 mb-3 px-3 py-2 rounded-lg border text-[12px]"
        style={{ borderColor: "var(--color-border)", background: "var(--color-bg-container)" }}
      >
        <ThunderboltOutlined className="text-[#1677ff] text-[14px]" />
        <span className="text-muted shrink-0">游戏路径</span>
        <span className="flex-1 truncate text-body font-mono">
          {gamePath || "未设置 — 首次一键启动时将提示选择"}
        </span>
        <Button
          size="small"
          icon={<FolderOpenOutlined />}
          loading={loadingGamePath}
          onClick={handleChangeGamePath}
        >
          {gamePath ? "更改" : "设置"}
        </Button>
      </div>

      {/* ── Content ── */}
      <div className="page-content thin-scrollbar">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <Spin size="default" />
          </div>
        ) : accounts.length > 0 ? (
          <div className="grid grid-cols-3 gap-3">
            {accounts.map((account, i) => {
              const info = getTypeInfo(account.type);
              const isActive = replaying === account.name || quickStarting === account.name;
              const isDragging = dragIdx === i;
              const showDropBefore = overIdx === i && dragIdx !== null && dragIdx > i;
              const showDropAfter = overIdx === i && dragIdx !== null && dragIdx < i;

              return (
                <div key={account.name} className="relative"
                  onDragOver={(e) => handleDragOver(e, i)}
                  onDrop={(e) => handleDrop(e, i)}>
                  {showDropBefore && (
                    <div className="absolute -top-1.5 left-0 right-0 h-0.5 rounded-full z-10"
                      style={{ background: "var(--color-primary, #1677ff)", boxShadow: "0 0 6px rgba(22,119,255,0.5)" }} />
                  )}
                  <div
                    className="account-card account-card-enter"
                    draggable
                    onDragStart={() => handleDragStart(i)}
                    onDragEnd={handleDragEnd}
                    style={{
                      animationDelay: `${i * 60}ms`,
                      borderTop: `3px solid ${info.color}`,
                      opacity: isDragging ? 0.4 : 1,
                      cursor: isDragging ? "grabbing" : "grab",
                      transition: "opacity 0.15s, transform 0.15s",
                      ...(isActive ? {
                        borderColor: info.color,
                        borderLeftColor: info.color,
                        borderRightColor: info.color,
                        borderBottomColor: info.color,
                        boxShadow: `0 0 0 1px ${info.color}40, 0 4px 16px ${info.color}18`,
                      } : {}),
                    }}
                  >
                    {/* Drag handle */}
                    <div className="absolute top-1.5 right-2 text-[#d0d4dc] hover:text-muted text-[13px] leading-none select-none"
                      style={{ cursor: "grab", opacity: 0, transition: "opacity 0.15s" }}
                      onMouseEnter={e => (e.currentTarget.style.opacity = "1")}
                      onMouseLeave={e => (e.currentTarget.style.opacity = "")}>
                      ⋮⋮
                    </div>
                  {/* Avatar + Identity */}
                  <div className="flex items-center gap-3 mb-3">
                    <div
                      className="account-avatar"
                      style={{
                        background: `linear-gradient(135deg, ${info.color}, ${info.color}cc)`,
                        boxShadow: `0 3px 8px ${info.color}30`,
                      }}
                    >
                      {account.name.charAt(0)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-[15px] font-semibold text-heading leading-tight truncate">
                        {account.name}
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span
                          className="text-[11px] px-1.5 py-px rounded font-medium"
                          style={{ color: info.color, background: info.bg }}
                        >
                          {info.label}
                        </span>
                        <span className="text-[11px] text-[#b0b5c0]">
                          {account.createdAt
                            ? new Date(account.createdAt).toLocaleDateString("zh-CN")
                            : "—"}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Separator */}
                  <div className="border-t border-[#f5f5f7] mb-2.5" />

                  {/* Actions */}
                  <div className="flex items-center gap-1">
                    <Tooltip title="一键启动">
                      <Button
                        type="primary"
                        size="small"
                        loading={quickStarting === account.name}
                        onClick={() => handleQuickStart(account.name)}
                        icon={<ThunderboltOutlined />}
                        className="text-[12px]"
                      >
                        启动
                      </Button>
                    </Tooltip>
                    <Tooltip title="回放登录">
                      <Button
                        size="small"
                        type="text"
                        icon={<PlayCircleOutlined />}
                        loading={replaying === account.name}
                        onClick={() => handleReplay(account.name)}
                      />
                    </Tooltip>
                    <div className="flex-1" />
                    <Tooltip title="重新录制">
                      <Button
                        size="small"
                        type="text"
                        icon={<ReloadOutlined />}
                        onClick={() => { setRecordName(account.name); setRecordMode((account.type as any) ?? "qr"); setRecordModalOpen(true); }}
                      />
                    </Tooltip>
                    <Popconfirm
                      title="确定删除此账号？"
                      onConfirm={() => handleDelete(account.name)}
                      okText="删除"
                      cancelText="取消"
                    >
                      <Button size="small" type="text" danger icon={<DeleteOutlined />} />
                    </Popconfirm>
                  </div>
                </div>
                {showDropAfter && (
                  <div className="absolute -bottom-1.5 left-0 right-0 h-0.5 rounded-full z-10"
                    style={{ background: "var(--color-primary, #1677ff)", boxShadow: "0 0 6px rgba(22,119,255,0.5)" }} />
                )}
                </div>
              );
            })}
          </div>
        ) : (
          /* ── Empty state ── */
          <div className="flex flex-col items-center justify-center h-full select-none">
            <div className="w-20 h-20 rounded-full bg-[#f5f7fa] flex items-center justify-center mb-5">
              <UserOutlined className="text-[32px] text-[#c8cdd5]" />
            </div>
            <div className="text-[14px] font-medium text-secondary mb-1">
              暂无账号
            </div>
            <div className="text-[12px] text-[#b0b5c0]">
              点击「录入账号」录制你的第一个游戏账号
            </div>
          </div>
        )}
      </div>

      {/* ── Record Modal ── */}
      <Modal
        title={
          <span className="flex items-center gap-2">
            <ScanOutlined className="text-[#1677ff]" />
            录入账号
          </span>
        }
        open={recordModalOpen}
        onCancel={closeRecord}
        footer={
          recording
            ? [<Button key="stop" danger onClick={stopRecording}>停止录制</Button>]
            : [
                <Button key="cancel" onClick={closeRecord}>取消</Button>,
                <Button key="start" type="primary" onClick={startRecording} disabled={!recordName.trim()}>
                  开始录制
                </Button>,
              ]
        }
        width={440}
      >
        <div className="flex flex-col gap-3 mt-2">
          <Input
            placeholder="输入账号名称（如：主号）"
            value={recordName}
            onChange={(e) => setRecordName(e.target.value)}
            disabled={recording}
          />
          {!recording && (
            <div>
              <div className="text-[12px] text-muted mb-2">登录方式</div>
              <Radio.Group
                value={recordMode}
                onChange={(e) => setRecordMode(e.target.value)}
                optionType="button"
                buttonStyle="solid"
                size="small"
              >
                <Radio.Button value="qr">
                  <ScanOutlined className="mr-1" />官服扫码
                </Radio.Button>
                <Radio.Button value="vivo">Vivo</Radio.Button>
                <Radio.Button value="bilibili">B站</Radio.Button>
                <Radio.Button value="huawei">华为</Radio.Button>
              </Radio.Group>
            </div>
          )}
          {recording && (
            <div className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg bg-[#f6f8fb] border border-[#eef0f2]">
              <Spin size="small" />
              <span className="text-[13px] text-secondary">{recordStatus}</span>
            </div>
          )}
          <div className="text-[12px] text-[#b0b5c0] leading-relaxed">
            {recordMode === "qr"
              ? "官服扫码：在游戏中手动登录，代理自动捕获登录凭证。"
              : `渠道服录制：在弹出的窗口中登录${{ vivo: "Vivo", bilibili: "B站", huawei: "华为" }[recordMode]}账号，然后在游戏中点击扫码登录。`}
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default AccountsPage;
