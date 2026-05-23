import type { FC } from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import { ReadOutlined, ReloadOutlined } from "@ant-design/icons";
import { message, Button, Input, Select, Space, Table, Tag } from "antd";
import type { ColumnsType, TablePaginationConfig } from "antd/es/table";
import { callApi } from "@/utils/pywebview";

interface LogEntry {
  timestamp: string;
  level: string;
  logger: string;
  message: string;
}

interface LogData {
  logs: LogEntry[];
  total: number;
  page: number;
  page_size: number;
}

const LEVEL_COLORS: Record<string, string> = {
  DEBUG: "default",
  INFO: "processing",
  WARNING: "warning",
  ERROR: "error",
  CRITICAL: "red",
};

const LogsPage: FC = () => {
  const [data, setData] = useState<LogData>({ logs: [], total: 0, page: 1, page_size: 30 });
  const [loading, setLoading] = useState(false);
  const [level, setLevel] = useState<string | undefined>(undefined);
  const [search, setSearch] = useState<string>("");
  const [scrollY, setScrollY] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const [inputValue, setInputValue] = useState("");

  const fetchLogs = useCallback(async (page = 1, pageSize = 30, filterLevel?: string, filterSearch?: string) => {
    setLoading(true);
    try {
      const result = await callApi<LogData>(
        "API:LOG:READ", page, pageSize, filterLevel ?? null, filterSearch || null,
      );
      if (result) setData(result);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLogs(1, data.page_size, level, search);
  }, [level, search]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver(() => {
      setScrollY(el.clientHeight - 110);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const handleTableChange = (pagination: TablePaginationConfig) => {
    fetchLogs(pagination.current ?? 1, pagination.pageSize ?? 30, level, search);
  };

  const handleSearch = (value: string) => {
    setSearch(value);
  };

  const columns: ColumnsType<LogEntry> = [
    {
      title: "时间戳",
      dataIndex: "timestamp",
      key: "timestamp",
      width: 200,
    },
    {
      title: "等级",
      dataIndex: "level",
      key: "level",
      width: 100,
      render: (lvl: string) => (
        <Tag color={LEVEL_COLORS[lvl] ?? "default"}>{lvl}</Tag>
      ),
    },
    {
      title: "信息",
      dataIndex: "message",
      key: "message",
      ellipsis: true,
    },
  ];

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-header__left">
          <span className="page-header__accent" />
          <h2 className="page-header__title">
            <ReadOutlined className="mr-2 text-[#1677ff]" />
            系统日志
          </h2>
        </div>
        <Space>
          <Select
            allowClear
            placeholder="日志等级"
            style={{ width: 120 }}
            value={level}
            onChange={(v) => setLevel(v)}
            options={["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"].map((l) => ({
              value: l,
              label: l,
            }))}
          />
          <Input.Search
            allowClear
            placeholder="搜索日志内容"
            style={{ width: 240 }}
            value={inputValue}
            onChange={(e) => {
              setInputValue(e.target.value);
              if (!e.target.value) setSearch("");
            }}
            onSearch={handleSearch}
          />
          <Button
            icon={<ReloadOutlined />}
            onClick={() => fetchLogs(1, data.page_size, level, search)}
          >
            刷新
          </Button>
        </Space>
      </div>

      <div ref={containerRef} className="page-content thin-scrollbar">
        <Table
          columns={columns}
          dataSource={data.logs}
          rowKey={(_, i) => String(i)}
          size="small"
          loading={loading}
          onChange={handleTableChange}
          scroll={{ y: scrollY }}
          onRow={(record) => ({
            style: { cursor: "pointer" },
            onClick: () => {
              const text = `[${record.timestamp}] [${record.level}] ${record.logger}: ${record.message}`;
              navigator.clipboard.writeText(text).then(() => {
                message.success("已复制到剪贴板", 1);
              });
            },
          })}
          pagination={{
            current: data.page,
            pageSize: data.page_size,
            total: data.total,
            showSizeChanger: true,
            showTotal: (t) => `共 ${t} 条`,
          }}
        />
      </div>
    </div>
  );
};

export default LogsPage;
