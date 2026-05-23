import { useState, useEffect, useRef, type FC } from "react";
import { Button, Input, Modal, Popconfirm, Table, Tooltip, message, Spin, Radio } from "antd";
import type { ColumnsType } from "antd/es/table";
import { PlusOutlined, DeleteOutlined, PlayCircleOutlined, ReloadOutlined, UserOutlined, ScanOutlined } from "@ant-design/icons";
import { useAccountStore } from "@/store/account-store";
import type { Account } from "@/store/account-store";

const AccountsPage: FC = () => {
  const accounts = useAccountStore((s) => s.accounts);
  const loading = useAccountStore((s) => s.loading);
  const loadAccounts = useAccountStore((s) => s.loadAccounts);

  useEffect(() => { loadAccounts(); }, []);

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

  const columns: ColumnsType<Account> = [
    {
      title: "账号名",
      dataIndex: "name",
      key: "name",
      width: 160,
      render: (name: string) => (
        <span className="font-medium text-[#1a1a2e]">{name}</span>
      ),
    },
    {
      title: "类型",
      dataIndex: "type",
      key: "type",
      width: 80,
      render: (t: string) => <span className="text-xs">{t || "官服"}</span>,
    },
    {
      title: "端口",
      dataIndex: "port",
      key: "port",
      width: 70,
      render: (p: number) => <span className="text-xs text-[#8b8fa3]">{p || 443}</span>,
    },
    {
      title: "创建时间",
      dataIndex: "createdAt",
      key: "createdAt",
      width: 150,
      render: (ts: number) => (
        <span className="text-xs text-[#8b8fa3]">
          {ts ? new Date(ts).toLocaleString("zh-CN") : "—"}
        </span>
      ),
    },
    {
      title: "操作",
      key: "action",
      width: 120,
      render: (_, record) => (
        <div className="flex items-center gap-1">
          <Tooltip title="一键启动">
            <Button
              type="text"
              size="small"
              loading={quickStarting === record.name}
              onClick={() => handleQuickStart(record.name)}
              icon={
                <svg viewBox="0 0 16 16" width="1em" height="1em">
                  <circle cx="8" cy="8" r="7.2" fill="none" stroke="currentColor" strokeWidth="1.2" />
                  <text x="8" y="8" textAnchor="middle" dominantBaseline="central" fontSize="9" fontWeight="700" fill="currentColor">糊</text>
                </svg>
              }
            />
          </Tooltip>
          <Button
            type="text"
            size="small"
            icon={<PlayCircleOutlined />}
            loading={replaying === record.name}
            onClick={() => handleReplay(record.name)}
          />
          <Button
            type="text"
            size="small"
            icon={<ReloadOutlined />}
            onClick={() => { setRecordName(record.name); setRecordMode("qr"); setRecordModalOpen(true); }}
            title="重新录制"
          />
          <Popconfirm
            title="确定删除此账号？"
            onConfirm={() => handleDelete(record.name)}
            okText="删除"
            cancelText="取消"
          >
            <Button type="text" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </div>
      ),
    },
  ];

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-header__left">
          <span className="page-header__accent" />
          <h2 className="page-header__title">
            <UserOutlined className="mr-2 text-[#1677ff]" />
            账号管理
          </h2>
          <span className="page-header__badge">
            {accounts.length}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setRecordModalOpen(true)}>
            录入账号
          </Button>
          {replaying && (
            <Button danger onClick={stopReplay}>
              停止回放
            </Button>
          )}
        </div>
      </div>

      <div className="page-content thin-scrollbar">
        <Table
          columns={columns}
          dataSource={accounts}
          rowKey="name"
          size="middle"
          pagination={false}
          loading={loading}
          locale={{ emptyText: "" }}
        />
      </div>

      <Modal
        title="录入账号"
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
        width={420}
      >
        <div className="flex flex-col gap-3 mt-2">
          <Input
            placeholder="输入账号名称（如：主号）"
            value={recordName}
            onChange={(e) => setRecordName(e.target.value)}
            disabled={recording}
          />
          {!recording && (
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
              <Radio.Button value="vivo">
                Vivo
              </Radio.Button>
              <Radio.Button value="bilibili">
                B站
              </Radio.Button>
              <Radio.Button value="huawei">
                华为
              </Radio.Button>
            </Radio.Group>
          )}
          {recording && (
            <div className="flex items-center gap-2 text-sm text-[#8b8fa3]">
              <Spin size="small" />
              <span>{recordStatus}</span>
            </div>
          )}
          <div className="text-xs text-[#bbb]">
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
