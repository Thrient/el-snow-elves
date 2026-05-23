import { type FC, type ReactNode, useEffect, useState, useRef, useCallback } from "react";
import { Table, Typography, Tag, Divider } from "antd";
import {
  BookOutlined,
  HomeOutlined,
  TableOutlined,
  CodeOutlined,
  ThunderboltOutlined,
  ApartmentOutlined,
  BuildOutlined,
  CalculatorOutlined,
  BranchesOutlined,
  ShareAltOutlined,
  ReloadOutlined,
  EyeOutlined,
  BulbOutlined,
  StarOutlined,
} from "@ant-design/icons";

const { Title, Paragraph, Text } = Typography;

/* ============================================================
   通用子组件
   ============================================================ */

const InlineCode: FC<{ children: string }> = ({ children }) => (
  <code className="px-1.5 py-0.5 text-[0.875em] bg-[#f0f2f5] text-[#d73a49] rounded font-mono font-medium">
    {children}
  </code>
);

const CodeBlock: FC<{ children: string; lang?: string }> = ({ children, lang = "json" }) => (
  <div className="rounded-xl overflow-hidden border border-[#e8eaed] my-4 shadow-sm">
    <div className="flex items-center justify-between px-4 py-2 bg-[#f8f9fa] border-b border-[#e8eaed]">
      <span className="text-[11px] font-semibold text-[#5f6368] uppercase tracking-wider">{lang}</span>
      <div className="flex gap-1.5">
        <span className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]" />
        <span className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]" />
        <span className="w-2.5 h-2.5 rounded-full bg-[#28ca41]" />
      </div>
    </div>
    <pre className="bg-[#1e1e1e] text-[#d4d4d4] p-4 m-0 text-[13px] leading-relaxed overflow-auto font-mono text-left whitespace-pre">
      {children}
    </pre>
  </div>
);

const Callout: FC<{ type: "tip" | "warn" | "info"; title?: string; children: ReactNode }> = ({ type, title, children }) => {
  const config = {
    tip:    { bg: "bg-emerald-50", border: "border-emerald-200", icon: <BulbOutlined className="text-emerald-600" />, title: title ?? "提示" },
    warn:   { bg: "bg-amber-50",   border: "border-amber-200",   icon: <ThunderboltOutlined className="text-amber-600" />,   title: title ?? "注意" },
    info:   { bg: "bg-sky-50",     border: "border-sky-200",     icon: <StarOutlined className="text-sky-600" />,          title: title ?? "说明" },
  }[type];
  return (
    <div className={`${config.bg} ${config.border} border rounded-xl px-4 py-3 my-4 flex items-start gap-3 text-sm`}>
      <span className="mt-0.5 flex-shrink-0">{config.icon}</span>
      <div>
        {config.title && <Text strong className="text-sm block mb-0.5">{config.title}</Text>}
        <div className="text-[#555]">{children}</div>
      </div>
    </div>
  );
};

const Section: FC<{ id: string; title: string; children: ReactNode }> = ({ id, title, children }) => (
  <section id={id} className="mb-12 scroll-mt-6">
    <Title level={4} className="!mb-5 !text-[17px] !font-semibold !tracking-tight">
      <span className="text-[#1677ff]/70 mr-2 font-mono text-sm">§</span>
      {title}
    </Title>
    {children}
  </section>
);

/* ============================================================
   侧边导航配置
   ============================================================ */

interface NavItem {
  id: string;
  label: string;
  icon: ReactNode;
}

const navItems: NavItem[] = [
  { id: "overview",       label: "项目概述",         icon: <HomeOutlined /> },
  { id: "json-structure", label: "JSON 结构总览",    icon: <TableOutlined /> },
  { id: "layout-fields",  label: "layout 配置面板",   icon: <BuildOutlined /> },
  { id: "step-fields",    label: "步骤定义字段",     icon: <CodeOutlined /> },
  { id: "action-types",   label: "action 动作类型",  icon: <ThunderboltOutlined /> },
  { id: "variables",      label: "变量系统",         icon: <ApartmentOutlined /> },
  { id: "expressions",    label: "表达式运算符",     icon: <CalculatorOutlined /> },
  { id: "control-flow",   label: "控制流程",         icon: <BranchesOutlined /> },
  { id: "reuse",          label: "公共步骤复用",     icon: <ShareAltOutlined /> },
  { id: "retry",          label: "retry 重试",       icon: <ReloadOutlined /> },
  { id: "monitors",       label: "后台监控",         icon: <EyeOutlined /> },
  { id: "patterns",       label: "常见编写模式",     icon: <BulbOutlined /> },
  { id: "quickref",       label: "快速查阅卡",       icon: <StarOutlined /> },
];

/* ============================================================
   主组件
   ============================================================ */

const DocsPage: FC = () => {
  const contentRef = useRef<HTMLDivElement>(null);
  const [activeId, setActiveId] = useState("overview");

  const scrollTo = useCallback((id: string) => {
    const el = document.getElementById(id);
    if (el && contentRef.current) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, []);

  // 滚动监听：高亮当前可见 section（使用视口坐标，避免 offsetParent 偏移导致末段无法选中）
  useEffect(() => {
    const container = contentRef.current;
    if (!container) return;

    let containerTop = container.getBoundingClientRect().top;

    const handleScroll = () => {
      const sections = navItems.map((n) => document.getElementById(n.id)).filter(Boolean) as HTMLElement[];

      for (let i = sections.length - 1; i >= 0; i--) {
        const rect = sections[i].getBoundingClientRect();
        if (rect.top <= containerTop + 80) {
          setActiveId(navItems[i].id);
          return;
        }
      }
    };

    const handleResize = () => {
      containerTop = container.getBoundingClientRect().top;
    };

    container.addEventListener("scroll", handleScroll, { passive: true });
    window.addEventListener("resize", handleResize);
    return () => {
      container.removeEventListener("scroll", handleScroll);
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  return (
    <div className="flex h-full bg-white">
      {/* ======= 左侧导航 ======= */}
      <aside className="w-[220px] flex-shrink-0 border-r border-[var(--color-border)] flex flex-col bg-[var(--color-bg-container)]">
        <div className="flex items-center gap-2.5 px-5 py-4 border-b border-[var(--color-border)]">
          <span className="flex items-center justify-center w-7 h-7 rounded-lg bg-[#1677ff] text-white">
            <BookOutlined className="text-sm" />
          </span>
          <div>
            <Text strong className="text-[13px] text-[#1a1a2e] leading-tight block">流程手册</Text>
            <Text className="text-[10px] text-[#999] leading-tight">Elves Reference</Text>
          </div>
        </div>

        <nav className="flex-1 overflow-auto py-3">
          {navItems.map((item) => {
            const isActive = activeId === item.id;
            return (
              <a
                key={item.id}
                onClick={(e) => { e.preventDefault(); scrollTo(item.id); }}
                className={`
                  flex items-center gap-2.5 mx-2 px-3 py-1.5 rounded-lg text-[13px] cursor-pointer
                  transition-colors duration-150 select-none
                  ${isActive
                    ? "bg-[#e6f4ff] text-[#1677ff] font-medium"
                    : "text-[#6b7280] hover:bg-[var(--color-bg-hover)] hover:text-[#1a1a2e]"
                  }
                `}
              >
                <span className={`text-sm flex-shrink-0 w-4 text-center ${isActive ? "text-[#1677ff]" : "text-[#bbb]"}`}>
                  {item.icon}
                </span>
                <span className="truncate">{item.label}</span>
              </a>
            );
          })}
        </nav>
      </aside>

      {/* ======= 右侧内容 ======= */}
      <div ref={contentRef} className="flex-1 overflow-y-auto">
        <div className="max-w-[820px] px-10 py-8">

          {/* 页头 */}
          <div className="mb-10">
            <div className="flex items-center gap-3 mb-3">
              <span className="flex items-center justify-center w-9 h-9 rounded-xl bg-[#1677ff] shadow-md shadow-blue-200">
                <CodeOutlined className="text-lg text-white" />
              </span>
              <Title level={2} className="!mb-0 !text-[22px] !font-bold !tracking-tight">流程编写参考手册</Title>
            </div>
            <Paragraph className="!text-[#666] !text-[15px] !mb-0">
              Elves 任务 JSON 的完整字段参考、语法说明与编写示例，从零基础到进阶全部覆盖。
            </Paragraph>
          </div>

          {/* 1. 项目概述 */}
          <Section id="overview" title="1. 项目概述">
            <Paragraph className="!text-[#444] !text-[14px]">
              Elves（时雪）是一套基于图像识别的桌面自动化工具。用户通过编写 <InlineCode>.json</InlineCode> 文件定义自动化流程，
              工具按流程定义自动截屏、匹配图像、模拟键鼠操作。
            </Paragraph>
            <Paragraph><Text strong>工作流 JSON 文件放置位置：</Text></Paragraph>
            <CodeBlock lang="path">{'{AppData}\\Elves\\Config\\User\\{任务名}.json'}</CodeBlock>
            <Paragraph className="mt-4"><Text strong>模板图片放置位置：</Text></Paragraph>
            <CodeBlock lang="path">{'resources\\config\\{任务名}\\{版本号}\\images\\{图片名}.bmp'}</CodeBlock>
            <Callout type="info">
              任务名必须与 JSON 文件名一致；模板图片格式统一为 BMP。
            </Callout>
          </Section>

          {/* 2. JSON 结构总览 */}
          <Section id="json-structure" title="2. JSON 结构总览">
            <Paragraph className="!text-[#444] !text-[14px]">一个完整的任务 JSON 包含以下顶层字段：</Paragraph>
            <div className="overflow-hidden rounded-xl border border-[#e8eaed]">
              <Table
                dataSource={[
                  { field: "name", type: "string", required: "是", desc: "任务名称，需与文件夹名一致" },
                  { field: "version", type: "string", required: "是", desc: "版本号，如 1.0.0" },
                  { field: "author", type: "string", required: "否", desc: "作者名" },
                  { field: "description", type: "string", required: "否", desc: "任务描述" },
                  { field: "start", type: "string", required: "是", desc: "入口步骤名，第一个执行的步骤" },
                  { field: "values", type: "object", required: "否", desc: "变量初始值，键值对，如 {\"count\": 0}" },
                  { field: "steps", type: "object", required: "是", desc: "步骤定义，键为步骤名，值为步骤配置对象" },
                  { field: "common", type: "object", required: "否", desc: "任务级公共步骤，覆盖全局 common.json 中的同名步骤" },
                  { field: "monitors", type: "object", required: "否", desc: "后台监控配置 {loop, interval}" },
                  { field: "layout", type: "array", required: "否", desc: "前端配置面板的表单布局定义" },
                  { field: "debug", type: "boolean", required: "否", desc: "启用详细调试日志" },
                ]}
                columns={[
                  { title: "字段", dataIndex: "field", key: "field", width: 105, render: (v: string) => <InlineCode>{v}</InlineCode> },
                  { title: "类型", dataIndex: "type", key: "type", width: 65, render: (v: string) => <Text className="text-[11px] text-[#999]">{v}</Text> },
                  { title: "必填", dataIndex: "required", key: "required", width: 50, render: (v: string) => <Tag color={v === "是" ? "red" : "default"} className="!text-[10px] !leading-none">{v}</Tag> },
                  { title: "说明", dataIndex: "desc", key: "desc", render: (v: string) => <span className="text-[13px]">{v}</span> },
                ]}
                rowKey="field"
                size="small"
                pagination={false}
              />
            </div>
          </Section>

          {/* 3. layout 配置面板 */}
          <Section id="layout-fields" title="3. layout 配置面板 — 表单控件参考">
            <Paragraph className="!text-[#444] !text-[14px]">
              <InlineCode>layout</InlineCode> 是任务 JSON 的顶层字段，定义前端配置面板的表单布局。它是一个二维数组，
              外层数组表示行，内层数组表示该行的控件。每个控件由 <InlineCode>Cell</InlineCode> 对象配置。
            </Paragraph>
            <CodeBlock>{`"layout": [
  [
    { "span": 12, "model": "el-switch", "text": "启用功能", "store": "enable_xxx" },
    { "span": 12, "model": "el-input-number", "text": "超时时间", "store": "timeout", "min": 100, "max": 10000 }
  ],
  [
    { "span": 24, "model": "el-select", "text": "策略", "store": "strategy",
      "options": [{ "label": "激进", "value": "aggressive" }, { "label": "保守", "value": "conservative" }] }
  ]
]`}</CodeBlock>

            <Divider className="!my-5" />
            <Text strong className="text-[14px] block mb-3">Cell 通用字段</Text>
            <div className="overflow-hidden rounded-xl border border-[#e8eaed]">
              <Table
                dataSource={[
                  { field: "span", type: "number", desc: "栅格宽度，每行总和通常为 24" },
                  { field: "model", type: "CellModel", desc: "控件类型，决定渲染哪个表单组件" },
                  { field: "text", type: "string", desc: "控件的标签文本" },
                  { field: "store", type: "string", desc: "绑定到 values 中的键名，控件值变化自动同步" },
                  { field: "disabled", type: "boolean", desc: "禁用控件" },
                  { field: "placeholder", type: "string", desc: "占位提示文本（Input / InputNumber / Select / DatePicker）" },
                  { field: "size", type: "string", desc: "控件尺寸：large | middle | small" },
                ]}
                columns={[
                  { title: "字段", dataIndex: "field", key: "field", width: 105, render: (v: string) => <InlineCode>{v}</InlineCode> },
                  { title: "类型", dataIndex: "type", key: "type", width: 85, render: (v: string) => <Text className="text-[11px] text-[#999]">{v}</Text> },
                  { title: "说明", dataIndex: "desc", key: "desc", render: (v: string) => <span className="text-[13px]">{v}</span> },
                ]}
                rowKey="field"
                size="small"
                pagination={false}
              />
            </div>

            <Divider className="!my-5" />
            <Text strong className="text-[14px] block mb-3">所有 model 类型一览</Text>
            <div className="overflow-hidden rounded-xl border border-[#e8eaed]">
              <Table
                dataSource={[
                  { model: "el-text",          component: "纯文本",        note: "仅展示，无交互，直接显示 text 内容" },
                  { model: "el-switch",        component: "Switch",       note: "开关，值为 boolean；支持 loading" },
                  { model: "el-input-number",  component: "InputNumber",  note: "数字输入，支持 min / max / step / precision / controls / readOnly" },
                  { model: "el-input",         component: "Input",        note: "文本输入，支持 allowClear / maxLength / showCount / readOnly" },
                  { model: "el-textarea",      component: "Input.TextArea", note: "多行文本，额外支持 rows / autoSize" },
                  { model: "el-checkbox",      component: "Checkbox",     note: "单个复选框，值为 boolean；text 作为子标签；支持 indeterminate" },
                  { model: "el-checkbox-group",component: "Checkbox.Group", note: "复选框组，值为数组；需 options；支持 disabled" },
                  { model: "el-radio",         component: "Radio.Group",  note: "单选组，需 options；支持 optionType (default|button) / buttonStyle (outline|solid)" },
                  { model: "el-select",        component: "Select",       note: "下拉选择，需 options；支持 allowClear / mode (multiple|tags) / showSearch / loading / maxTagCount" },
                  { model: "el-slider",        component: "Slider",       note: "滑动条，支持 min / max / step / dots / marks / range / vertical / included" },
                  { model: "el-date-picker",   component: "DatePicker",   note: "日期选择，值为字符串；支持 format / picker / showTime / allowClear" },
                  { model: "el-color-picker",  component: "ColorPicker",  note: "颜色选择，值为 hex 字符串；支持 format (hex|rgb|hsb) / showText / allowClear" },
                  { model: "el-key-input",     component: "KeyInput",     note: "按键捕获输入，按下键盘自动记录键名；值为 key 字符串如 Enter / Num0 / A" },
                ]}
                columns={[
                  { title: "model", dataIndex: "model", key: "model", width: 155, render: (v: string) => <InlineCode>{v}</InlineCode> },
                  { title: "组件", dataIndex: "component", key: "component", width: 125, render: (v: string) => <Text className="text-[13px] font-medium">{v}</Text> },
                  { title: "说明", dataIndex: "note", key: "note", render: (v: string) => <span className="text-[13px]">{v}</span> },
                ]}
                rowKey="model"
                size="small"
                pagination={false}
              />
            </div>

            <Callout type="info" title="options 格式">
              适用于 <InlineCode>el-select</InlineCode> / <InlineCode>el-radio</InlineCode> / <InlineCode>el-checkbox-group</InlineCode>：
              <CodeBlock>{`"options": [
  { "label": "显示文本", "value": "存储值" },
  { "label": "选项二",   "value": 2 }
]`}</CodeBlock>
              <InlineCode>value</InlineCode> 支持 <InlineCode>string</InlineCode> 和 <InlineCode>number</InlineCode>。
            </Callout>
          </Section>

          {/* 4. 步骤定义 */}
          <Section id="step-fields" title="4. 步骤定义 — 所有可写字段">
            <Paragraph className="!text-[#444] !text-[14px]">
              每个步骤是一个 JSON 对象。<InlineCode>action</InlineCode> 决定执行什么操作，其余字段控制跳转、恢复、变量操作。
            </Paragraph>
            <div className="overflow-hidden rounded-xl border border-[#e8eaed]">
              <Table
                dataSource={[
                  { field: "action",     required: "是", desc: "动作类型（touch/exits/key_click 等），也支持 {表达式} 做条件判断" },
                  { field: "params",     required: "否", desc: "传给 action 的参数，所有字段值都支持 {} 变量语法" },
                  { field: "prefix",     required: "否", desc: "执行 action 之前运行的子流程列表" },
                  { field: "postfix",    required: "否", desc: "执行 action 之后运行的子流程列表（无论成败都执行）" },
                  { field: "success",    required: "否", desc: "action 成功（返回非空）时跳转的目标步骤名，优先级最高" },
                  { field: "failure",    required: "否", desc: "action 失败（返回空）时跳转的目标步骤名" },
                  { field: "next",       required: "否", desc: "无论成败都跳转的目标步骤名，被 success/failure 覆盖" },
                  { field: "failure_extra", required: "否", desc: "仅在 action 失败时执行的恢复子流程。配合 retry 每次重试前都会执行" },
                  { field: "success_extra", required: "否", desc: "仅在 action 成功时执行的一次性子流程" },
                  { field: "set",        required: "否", desc: "步骤执行后更新变量，每项 {name, value}，value 支持 {} 语法" },
                  { field: "retry",      required: "否", desc: "失败重试配置 {times: 最大次数, interval: 重试间隔 ms}" },
                  { field: "extends",    required: "否", desc: "继承另一个步骤的全部字段（params 浅合并），当前字段覆盖父步骤" },
                ]}
                columns={[
                  { title: "字段", dataIndex: "field", key: "field", width: 120, render: (v: string) => <InlineCode>{v}</InlineCode> },
                  { title: "必填", dataIndex: "required", key: "required", width: 48, render: (v: string) => <Tag color={v === "是" ? "red" : "default"} className="!text-[10px] !leading-none">{v}</Tag> },
                  { title: "说明", dataIndex: "desc", key: "desc", render: (v: string) => <span className="text-[13px]">{v}</span> },
                ]}
                rowKey="field"
                size="small"
                pagination={false}
              />
            </div>
            <div className="mt-4 p-4 rounded-xl bg-[#fafbfc] border border-[#e8eaed] text-[13px] space-y-1">
              <Text strong className="text-[13px]">跳转优先级</Text>
              <div className="font-mono text-[#555]">
                action 返回结果后 → <span className="text-[#1677ff]">success</span> → <span className="text-[#1677ff]">failure</span> → <span className="text-[#1677ff]">next</span> → <span className="text-[#d73a49]">"任务结束"</span>
              </div>
            </div>
          </Section>

          {/* 5. action 类型 */}
          <Section id="action-types" title="5. action 动作类型参考">
            <Paragraph className="!text-[#444] !text-[14px]">支持 7 种 action（含表达式占位）：</Paragraph>
            <div className="overflow-hidden rounded-xl border border-[#e8eaed]">
              <Table
                dataSource={[
                  { action: "touch",          desc: "截屏匹配模板，找到后点击。循环匹配直到找到或超时",                           returns: "坐标列表 [[x,y],...]，失败 []" },
                  { action: "exits",          desc: "截屏匹配模板，仅检测是否存在不点击。适用于条件判断",                         returns: "坐标列表，失败 []" },
                  { action: "wait",           desc: "等待模板出现在屏幕上。用于等待界面加载、按钮出现等场景",                    returns: "坐标列表，找到后立即返回" },
                  { action: "wait_disappear", desc: "等待模板从屏幕上消失。用于等待寻路结束、战斗状态消失等",                    returns: "消失 → 最后坐标，超时 → None" },
                  { action: "exits_color",         desc: "截图并检测区域内是否存在目标颜色。RGB 欧氏距离 ≤ 容差即匹配",         returns: "True(存在) / False(不存在)" },
                  { action: "touch_color",         desc: "在区域内搜索目标颜色，找到后点击。循环匹配直到找到或超时",              returns: "坐标列表，失败 []" },
                  { action: "wait_color",          desc: "等待目标颜色出现在屏幕上。用于等待血量变化、技能冷却结束等",          returns: "坐标列表，找到后立即返回" },
                  { action: "wait_color_disappear",desc: "等待目标颜色从屏幕上消失。用于等待加载画面消失、状态结束等",          returns: "消失 → True，超时 → None" },
                  { action: "key_click",      desc: "模拟键盘按键，支持 A~Z / ENTER / ESCAPE / SPACE / TAB / DIGIT0~9 等",        returns: "None" },
                  { action: "mouse_click",    desc: "模拟鼠标左键点击指定屏幕坐标",                                              returns: "None" },
                  { action: "mouse_drag",    desc: "模拟鼠标拖拽：从起始坐标拖拽到终点坐标，支持平滑插值",                    returns: "None" },
                  { action: "{表达式}",       desc: "不对屏幕做任何操作，仅对表达式求值，结果（布尔）用于流程跳转",             returns: "True / False" },
                ]}
                columns={[
                  { title: "", dataIndex: "action", key: "action", width: 135, render: (v: string) => <InlineCode>{v}</InlineCode> },
                  { title: "说明", dataIndex: "desc", key: "desc", render: (v: string) => <span className="text-[13px]">{v}</span> },
                  { title: "返回值", dataIndex: "returns", key: "returns", width: 190, render: (v: string) => <span className="text-[12px] text-[#888]">{v}</span> },
                ]}
                rowKey="action"
                size="small"
                pagination={false}
              />
            </div>

            <Divider className="!my-5" />
            <Text strong className="text-[14px] block mb-3">params 通用参数详解</Text>
            <div className="overflow-hidden rounded-xl border border-[#e8eaed]">
              <Table
                dataSource={[
                  { param: "args",        type: "[string]",           act: "touch / exits / wait / wait_disappear", desc: "模板图片名列表（不含路径和 .bmp），支持 {变量} 嵌入" },
                  { param: "threshold",   type: "number",             act: "touch / exits / wait / wait_disappear", desc: "匹配置信度阈值 0~1，默认 0.85。越高越严（误匹配少），越低越宽" },
                  { param: "color",       type: "[R,G,B]",            act: "exits_color / touch_color / wait_color / wait_color_disappear", desc: "目标颜色 [红, 绿, 蓝]，如 [255, 0, 0] 正红" },
                  { param: "tolerance",   type: "number",             act: "exits_color / touch_color / wait_color / wait_color_disappear", desc: "颜色容差 0-255，默认 10。RGB 欧氏距离 ≤ 此值视为匹配" },
                  { param: "seconds",     type: "number | null",      act: "touch / wait / wait_disappear / wait_color / wait_color_disappear", desc: "最大等待秒数。touch 默认 1.8s，wait 默认 1s。填 0 则使用默认值" },
                  { param: "box",         type: "[x1,y1,x2,y2]",      act: "touch / exits / wait / wait_disappear / 全部颜色动作", desc: "搜索区域限制，默认 [0,0,1335,750]，缩小可提速" },
                  { param: "click_mode",  type: "string",             act: "touch",                          desc: "点击策略：random（默认）/ first / last / all / all_reverse" },
                  { param: "x / y",       type: "number",             act: "touch / mouse_click / mouse_drag", desc: "点击/拖拽起始坐标在匹配位置上的偏移量" },
                  { param: "k",           type: "number",             act: "wait_disappear",                 desc: "连续确认消失帧数，默认 1。设为 6 需连续 6 帧未匹配才确认" },
                  { param: "key",         type: "string",             act: "key_click",                      desc: "按键名，支持 {CONFIG.键名} 引用全局设置" },
                  { param: "pos",         type: "[x,y]",              act: "mouse_click",                    desc: "点击的屏幕绝对坐标，如 [1335, 711]" },
                  { param: "start_pos",   type: "[x,y]",              act: "mouse_drag",                     desc: "拖拽起始坐标，如 [100, 200]" },
                  { param: "end_pos",     type: "[x,y]",              act: "mouse_drag",                     desc: "拖拽终点坐标，如 [300, 400]" },
                  { param: "end_x / end_y", type: "number",           act: "mouse_drag",                     desc: "拖拽终点的坐标偏移量，默认 0" },
                  { param: "duration",    type: "number",             act: "mouse_drag",                     desc: "拖拽持续时间（秒），越大越慢越平滑，默认 0.5" },
                  { param: "count",       type: "number",             act: "key_click / mouse_click / mouse_drag / touch / touch_color", desc: "重复次数，默认 1" },
                  { param: "pre_delay",   type: "number",             act: "全部",                           desc: "操作前延迟等待（ms），默认 1500" },
                  { param: "post_delay",  type: "number",             act: "全部",                           desc: "操作后延迟等待（ms），默认 1500" },
                  { param: "preprocess",  type: "object",             act: "touch / exits / wait / wait_disappear", desc: "图像预处理配置，独立开关组合。详见 §5.1" },
                ]}
                columns={[
                  { title: "参数", dataIndex: "param", key: "param", width: 120, render: (v: string) => <InlineCode>{v}</InlineCode> },
                  { title: "类型", dataIndex: "type", key: "type", width: 105, render: (v: string) => <span className="text-[11px] text-[#999] font-mono">{v}</span> },
                  { title: "适用", dataIndex: "act", key: "act", width: 175, render: (v: string) => <span className="text-[11px] text-[#999]">{v}</span> },
                  { title: "说明", dataIndex: "desc", key: "desc", render: (v: string) => <span className="text-[13px]">{v}</span> },
                ]}
                rowKey="param"
                size="small"
                pagination={false}
              />
            </div>
            <Divider className="!my-5" />
            <Text strong className="text-[14px] block mb-3" id="preprocess-detail">§5.1 图像预处理（preprocess）详细参考</Text>
            <Paragraph className="!text-[#444] !text-[14px]">
              预处理所有字段均为独立开关，不设则默认不启用。可自由组合（如二值化 + 反转）。
            </Paragraph>
            <div className="overflow-hidden rounded-xl border border-[#e8eaed]">
              <Table
                dataSource={[
                  { param: "binarize",            type: "bool",   default: "false",  desc: "二值化。将灰度图转为纯黑白，消除纹理干扰。阈值由 binarize_threshold 控制（0=OTSU自动）" },
                  { param: "binarize_threshold",  type: "0-255",  default: "0",      desc: "二值化固定阈值。0 时用 OTSU 自动计算。推荐范围 100-180，值越大黑色越多" },
                  { param: "binarize_invert",     type: "bool",   default: "false",  desc: "反转二值化结果（黑变白/白变黑）。适合亮色目标在暗色背景上的场景" },
                  { param: "adaptive",            type: "bool",   default: "false",  desc: "自适应高斯阈值。将图像分成小块独立计算阈值，适合光照不均、渐变背景。与 binarize 互斥（优先）" },
                  { param: "adaptive_block",      type: "奇数",   default: "11",     desc: "自适应阈值块大小（像素）。值越小越敏感但噪声越多。推荐范围 9-15" },
                  { param: "adaptive_c",          type: "2-10",   default: "2",      desc: "自适应阈值常数，从每块均值中减去。值越大匹配越宽松。推荐范围 2-5" },
                ]}
                columns={[
                  { title: "字段", dataIndex: "param", key: "param", width: 150, render: (v: string) => <InlineCode>{v}</InlineCode> },
                  { title: "类型", dataIndex: "type", key: "type", width: 60, render: (v: string) => <span className="text-[11px] text-[#999] font-mono">{v}</span> },
                  { title: "默认", dataIndex: "default", key: "default", width: 55, render: (v: string) => <span className="text-[11px] text-[#999]">{v}</span> },
                  { title: "说明", dataIndex: "desc", key: "desc", render: (v: string) => <span className="text-[13px]">{v}</span> },
                ]}
                rowKey="param"
                size="small"
                pagination={false}
              />
            </div>
            <div className="mt-4 space-y-3">
              <Text strong className="text-[14px] block">使用示例</Text>
              <CodeBlock>{`// 仅 OTSU 二值化（最常用）
"preprocess": { "binarize": true }

// 固定阈值 150 二值化
"preprocess": { "binarize": true, "binarize_threshold": 150 }

// 二值化 + 反转（亮底暗字 → 暗底亮字）
"preprocess": { "binarize": true, "binarize_invert": true }

// 自适应阈值（光照不均场景）
"preprocess": { "adaptive": true }

// 自适应 + 调参
"preprocess": { "adaptive": true, "adaptive_block": 15, "adaptive_c": 3 }

// 仅反转（不做二值化，直接反转灰度）
"preprocess": { "binarize_invert": true }`}</CodeBlock>
              <Callout type="tip" title="调试建议">
                如果某种预处理导致一直匹配不上，直接删掉对应字段或设为 <InlineCode>false</InlineCode> 即可。每个开关独立控制，互不影响。
              </Callout>
            </div>
          </Section>

          {/* 6. 变量系统 */}
          <Section id="variables" title="6. 变量系统 — 所有 {} 语法">
            <Paragraph className="!text-[#444] !text-[14px]">
              在 <InlineCode>params</InlineCode> 的任意字段值、<InlineCode>action</InlineCode>、<InlineCode>set[].value</InlineCode> 中均可使用花括号语法。
            </Paragraph>
            <div className="overflow-hidden rounded-xl border border-[#e8eaed]">
              <Table
                dataSource={[
                  { syntax: "{变量名}",              desc: "引用变量值，变量不存在则报 NameError",                                       place: "params / set" },
                  { syntax: "{result}",             desc: "上一步 action 的返回值（坐标列表或布尔值），仅在 set 中可用",                place: "set" },
                  { syntax: "{变量名}++",           desc: "变量自增 1 返回新值，-- 同理（变量必须是数字）",                              place: "set" },
                  { syntax: "{变量:默认值}",        desc: "变量不存在时用默认值。支持数字、数组、字符串、布尔",                          place: "params" },
                  { syntax: "{表达式}",             desc: "安全表达式求值：算术 + 比较 + 布尔 + 下标 + 属性访问",                       place: "action / set" },
                  { syntax: "文本{变量}文本",       desc: "变量值嵌入字符串模板，用于动态拼接 args 模板名",                             place: "params.args" },
                  { syntax: "{CONFIG.键名}",        desc: "引用全局设置中的用户配置值（前端「全局设置」管理）",                          place: "params key" },
                ]}
                columns={[
                  { title: "语法", dataIndex: "syntax", key: "syntax", width: 165, render: (v: string) => <InlineCode>{v}</InlineCode> },
                  { title: "说明", dataIndex: "desc", key: "desc", render: (v: string) => <span className="text-[13px]">{v}</span> },
                  { title: "位置", dataIndex: "place", key: "place", width: 110, render: (v: string) => <Tag color="blue" className="!text-[10px]">{v}</Tag> },
                ]}
                rowKey="syntax"
                size="small"
                pagination={false}
              />
            </div>
            <Callout type="tip" title="变量来源">
              <ul className="list-disc pl-4 space-y-0.5 m-0">
                <li><InlineCode>values</InlineCode> — 任务 JSON 顶层定义的初始值</li>
                <li><InlineCode>set</InlineCode> — 步骤执行后通过 set 数组动态赋值</li>
                <li><InlineCode>CONFIG</InlineCode> — 全局设置页面配置的值，运行时自动注入</li>
                <li>子流程传参 — 调用时通过 <InlineCode>args</InlineCode> 对象传入，合并到变量表</li>
              </ul>
            </Callout>
          </Section>

          {/* 7. 表达式 */}
          <Section id="expressions" title="7. 表达式运算符参考">
            <Paragraph className="!text-[#444] !text-[14px]">
              编写 <InlineCode>{"{表达式}"}</InlineCode> 时，所有运算在安全沙箱中执行，仅允许白名单操作：
            </Paragraph>
            <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-4">
              {[
                { label: "算术", ops: "+  -  *  /  //  %  **" },
                { label: "比较", ops: "==  !=  <  >  <=  >=" },
                { label: "布尔", ops: "and  or  not" },
                { label: "常量", ops: "True  False  None" },
                { label: "访问", ops: "dict.key  list[0]" },
              ].map(({ label, ops }) => (
                <div key={label} className="bg-[#fafbfc] border border-[#e8eaed] rounded-xl px-4 py-3">
                  <Text className="text-[10px] text-[#aaa] uppercase tracking-wider font-semibold">{label}</Text>
                  <div className="mt-1 font-mono text-[13px] text-[#333] leading-relaxed">{ops}</div>
                </div>
              ))}
            </div>
            <Callout type="tip" title="典型示例">
              <ul className="list-disc pl-4 space-y-0.5 m-0 font-mono text-[13px]">
                <li><InlineCode>{"{count >= 3}"}</InlineCode> <span className="text-[#888] font-sans">— 计数是否达到上限（循环退出条件）</span></li>
                <li><InlineCode>{"{flag and not done}"}</InlineCode> <span className="text-[#888] font-sans">— 标记为真且未完成</span></li>
                <li><InlineCode>{"{result[0][0] > 500}"}</InlineCode> <span className="text-[#888] font-sans">— 第一个匹配的 x 坐标大于 500</span></li>
                <li><InlineCode>{"{hp > 0.5 or shield > 0}"}</InlineCode> <span className="text-[#888] font-sans">— 血量过半或有护盾</span></li>
              </ul>
            </Callout>
          </Section>

          {/* 8. 控制流程 */}
          <Section id="control-flow" title="8. 控制流程 — 步骤如何跳转">
            <Paragraph className="!text-[#444] !text-[14px]">每个步骤按以下顺序执行：</Paragraph>
            <div className="bg-[#fafbfc] rounded-xl border border-[#e8eaed] overflow-hidden">
              <div className="bg-[#1e1e1e] px-4 py-2 flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]" />
                <span className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]" />
                <span className="w-2.5 h-2.5 rounded-full bg-[#28ca41]" />
                <span className="text-[11px] text-[#888] ml-2 font-mono">步骤生命周期</span>
              </div>
              <div className="p-5 font-mono text-[13px] leading-loose">
                {[
                  ["prefix",     "执行前置子流程（顺序执行，不影响 action）"],
                  ["action",     "主操作（含 retry 重试循环，每次失败执行 failure_extra）"],
                  ["set",        "变量更新（处理后存入变量表供后续步骤使用）"],
                  ["postfix",    "执行后置子流程（顺序执行，无论成败）"],
                  ["extra",      "成功 → success_extra；失败且无 retry → failure_extra"],
                  ["jump",       "决定下一步：success → failure → next → \"任务结束\""],
                ].map(([tag, desc], i) => (
                  <div key={tag} className="flex items-start gap-3">
                    <span className="text-[#999] w-8 text-right flex-shrink-0">{i + 1}</span>
                    <span className="text-[#d73a49] font-semibold w-20 flex-shrink-0">{tag}</span>
                    <span className="text-[#666]">{desc}</span>
                  </div>
                ))}
              </div>
            </div>
            <Divider className="!my-4" />
            <Text strong className="text-[14px] block mb-2">子流程列表项支持 5 种写法：</Text>
            <div className="grid grid-cols-2 gap-2 mb-4">
              {[
                ["纯名称", '"步骤名"'],
                ["重复 N 次", '"步骤名*8"'],
                ["带参数", '{"step":"步骤名", "args":{...}}'],
                ["传参 + 重复", '{"step":"步骤名*5", "args":{...}}'],
                ["条件执行", '{"step":"步骤名", "when":"{表达式}"}'],
              ].map(([label, code]) => (
                <div key={label} className="bg-[#fafbfc] border border-[#e8eaed] rounded-lg px-3 py-2 flex items-center gap-2">
                  <Tag className="!text-[10px] !m-0 flex-shrink-0">{label}</Tag>
                  <InlineCode>{code}</InlineCode>
                </div>
              ))}
            </div>
            <Callout type="info" title="when 条件说明">
              <InlineCode>when</InlineCode> 仅在 dict 格式中可用，值为 <InlineCode>{"{表达式}"}</InlineCode> 或 <InlineCode>{"{变量名}"}</InlineCode>。
              子流程执行前先对其求值，结果为 <InlineCode>False</InlineCode> / <InlineCode>0</InlineCode> / <InlineCode>None</InlineCode> / 空时跳过不执行。
              <strong className="text-[13px] block mt-2">典型用法：</strong>
              <ul className="list-disc pl-4 space-y-0.5 m-0 mt-1 text-[13px]">
                <li><InlineCode>{"when: \"{count >= 3}\""}</InlineCode> — 计数达标才执行</li>
                <li><InlineCode>{"when: \"{need_check}\""}</InlineCode> — 标记为真才执行</li>
                <li><InlineCode>{"when: \"{retry_count > 1 and retry_count % 3 == 0}\""}</InlineCode> — 每 3 次重试执行一次</li>
              </ul>
            </Callout>
          </Section>

          {/* 9. 公共步骤复用 */}
          <Section id="reuse" title="9. 如何复用公共步骤">
            <Paragraph className="!text-[#444] !text-[14px]">三种复用方式，按场景选择：</Paragraph>

            <Text strong className="text-[14px] block mb-2">方式一：extends 继承</Text>
            <Paragraph className="!text-[#666] !text-[13px]">适合"参数大部分相同，只改一两个"的场景。params 浅合并，子覆盖父。</Paragraph>
            <CodeBlock>{`"关闭窗口": {
  "action": "touch",
  "params": { "args": ["V1","V2","V3","V4","V5"], "threshold": 0.85 }
},
"关闭奖励弹窗": {
  "extends": "关闭窗口",
  "params": { "box": [905, 201, 1118, 900] }
}`}</CodeBlock>

            <Divider className="!my-5" />
            <Text strong className="text-[14px] block mb-2">方式二：{"{变量:默认值}"} + 传参</Text>
            <Paragraph className="!text-[#666] !text-[13px]">适合"调用方决定关键参数"的场景。common 定义通用模板，调用方传参覆盖。</Paragraph>
            <CodeBlock>{`// common.json
"打开面板": {
  "action": "touch",
  "params": { "args": ["{面板按钮:按钮物品综合入口}"] },
  "next": "任务结束"
}

// 调用方传参
"prefix": [
  { "step": "打开面板", "args": { "面板按钮": "按钮活动江湖" } }
]`}</CodeBlock>

            <Divider className="!my-5" />
            <Text strong className="text-[14px] block mb-2">方式三：模板名模式化</Text>
            <Paragraph className="!text-[#666] !text-[13px]">适合"一批模板名结构相同，只有中间某段不同"的场景。</Paragraph>
            <CodeBlock>{`"params": {
  "args": ["按钮{前缀}止杀", "按钮{前缀}锻心", "按钮{前缀}问卜"]
}
// 传 { "前缀": "任务" } → 匹配 按钮任务止杀, 按钮任务锻心, 按钮任务问卜`}</CodeBlock>
          </Section>

          {/* 10. retry 重试 */}
          <Section id="retry" title="10. retry 重试机制">
            <Paragraph className="!text-[#444] !text-[14px]">
              添加 <InlineCode>retry</InlineCode> 字段，action 失败后执行 <InlineCode>failure_extra</InlineCode> 恢复，然后重试：
            </Paragraph>
            <CodeBlock>{`"检查背包": {
  "action": "exits",
  "params": { "args": ["界面物品"] },
  "retry": { "times": 3, "interval": 500 },
  "failure_extra": ["检测主界面", "打开背包"],
  "failure": "任务结束"
}`}</CodeBlock>
            <Callout type="info">
              <strong className="text-[13px]">执行流程：</strong>action 失败 → failure_extra 恢复 → 等 interval ms → 重试 → 最多 times 次 → 全部失败才跳 failure。<br />
              retry 是步骤级重试（每次重新截屏匹配），与 touch 内部的 seconds（单次持续匹配时长）不冲突。
            </Callout>
          </Section>

          {/* 11. monitors */}
          <Section id="monitors" title="11. monitors 后台监控">
            <Paragraph className="!text-[#444] !text-[14px]">任务运行期间启动后台线程，循环执行操作：</Paragraph>
            <CodeBlock>{`"monitors": {
  "loop": ["一键提交"],
  "interval": 1
}`}</CodeBlock>
            <Paragraph className="!text-[#666] !text-[13px] mt-3">
              <InlineCode>loop</InlineCode> — 循环执行的步骤名列表；<InlineCode>interval</InlineCode> — 每轮间隔秒数。
            </Paragraph>
            <Callout type="info">
              监控线程以守护线程启动，任务主流程走到 "任务结束" 时自动停止。
            </Callout>
          </Section>

          {/* 12. 常见模式 */}
          <Section id="patterns" title="12. 常见编写模式">

            <Text strong className="text-[14px] block mb-1">模式一：条件分支</Text>
            <Paragraph className="!text-[#888] !text-[13px] !mb-2">根据模板是否出现决定走哪条路径。</Paragraph>
            <CodeBlock>{`"检查": {
  "action": "exits",
  "params": { "args": ["某按钮"] },
  "success": "处理A",
  "failure": "处理B"
}`}</CodeBlock>

            <Divider className="!my-5" />
            <Text strong className="text-[14px] block mb-1">模式二：自循环检测（无限重试）</Text>
            <Paragraph className="!text-[#888] !text-[13px] !mb-2">不用 retry，failure 指回自己实现无限等待。适合不确定出现时机的场景。</Paragraph>
            <CodeBlock>{`"检测": {
  "action": "exits",
  "params": { "args": ["目标"] },
  "failure_extra": ["恢复操作"],
  "failure": "检测"
}`}</CodeBlock>

            <Divider className="!my-5" />
            <Text strong className="text-[14px] block mb-1">模式三：固定次数重试</Text>
            <Paragraph className="!text-[#888] !text-[13px] !mb-2">有限重试，超限后走备选路径。</Paragraph>
            <CodeBlock>{`"检测": {
  "action": "exits",
  "params": { "args": ["目标"] },
  "retry": { "times": 3, "interval": 500 },
  "failure_extra": ["恢复操作"],
  "failure": "下次尝试"
}`}</CodeBlock>

            <Divider className="!my-5" />
            <Text strong className="text-[14px] block mb-1">模式四：等待动态场景消失</Text>
            <Paragraph className="!text-[#888] !text-[13px] !mb-2">等待寻路动画、战斗中标志消失。k 值越大越可靠但越慢。</Paragraph>
            <CodeBlock>{`"等待寻路完成": {
  "action": "wait_disappear",
  "params": {
    "args": ["标志寻路中","标志战斗中","标志地图加载_V1"],
    "seconds": 180,
    "k": 6
  },
  "next": "任务结束"
}`}</CodeBlock>

            <Divider className="!my-5" />
            <Text strong className="text-[14px] block mb-1">模式五：变量计数 + 表达式分支</Text>
            <Paragraph className="!text-[#888] !text-[13px] !mb-2">用 set 维护计数器，用 {"{表达式}"} 做循环退出判断。</Paragraph>
            <CodeBlock>{`"values": { "count": 0 },
"尝试": {
  "action": "touch",
  "params": { "args": ["目标"], "seconds": null },
  "set": [{ "name": "count", "value": "{count}++" }],
  "failure": "放弃",
  "success": "下一步"
},
"放弃": {
  "action": "{count < 3}",
  "success": "尝试",
  "failure": "任务结束"
}`}</CodeBlock>
          </Section>

          {/* 13. 快速查阅卡 */}
          <Section id="quickref" title="13. 快速查阅卡">
            <div className="rounded-xl border-2 border-[#e6f4ff] bg-gradient-to-br from-[#f0f7ff] to-white p-6">
              <Paragraph className="!text-[#1a1a2e] !font-semibold !text-[14px] !mb-4">
                写一个步骤 = 决定 5 件事
              </Paragraph>
              <div className="space-y-3">
                {[
                  { color: "blue",   icon: <ThunderboltOutlined />, label: "做什么",  detail: "选 action 类型 + 填 params 参数" },
                  { color: "green",  icon: <BranchesOutlined />,    label: "前后",   detail: "用 prefix / postfix 做前置准备和收尾" },
                  { color: "orange", icon: <ShareAltOutlined />,    label: "去哪",   detail: "用 success / failure / next 控制跳转" },
                  { color: "red",    icon: <ReloadOutlined />,      label: "恢复",   detail: "用 failure_extra + retry 失败恢复和重试" },
                  { color: "purple", icon: <ApartmentOutlined />,   label: "复用",   detail: "用 extends 或 {变量:默认值} 避免重复" },
                ].map(({ color, icon, label, detail }) => (
                  <div key={label} className="flex items-center gap-3">
                    <Tag color={color} className="!text-[11px] !py-0.5 !px-2 flex-shrink-0 min-w-[50px] text-center">
                      {icon} {label}
                    </Tag>
                    <span className="text-[13px] text-[#555]">{detail}</span>
                  </div>
                ))}
              </div>
            </div>
          </Section>

        </div>
      </div>
    </div>
  );
};

export default DocsPage;
