import { type FC, type ReactNode, useEffect, useState, useRef, useCallback } from "react";
import { Typography, Tag, Divider } from "antd";
import {
  HomeOutlined,
  BuildOutlined,
  ApartmentOutlined,
  CodeOutlined,
  ThunderboltOutlined,
  BranchesOutlined,
  ShareAltOutlined,
  EyeOutlined,
  BulbOutlined,
  StarOutlined,
  EditOutlined,
  ToolOutlined,
} from "@ant-design/icons";

const { Title, Paragraph, Text } = Typography;

/* ============================================================
   通用子组件（与 DocsPage 一致）
   ============================================================ */

const InlineCode: FC<{ children: string }> = ({ children }) => (
  <code className="px-1.5 py-0.5 text-[0.875em] bg-[#f0f2f5] text-[#d73a49] rounded font-mono font-medium">
    {children}
  </code>
);
const Callout: FC<{ type: "tip" | "warn" | "info"; title?: string; children: ReactNode }> = ({ type, title, children }) => {
  const config = {
    tip:  { bg: "bg-emerald-50", border: "border-emerald-200", icon: <BulbOutlined className="text-emerald-600" />, title: title ?? "提示" },
    warn: { bg: "bg-amber-50",   border: "border-amber-200",   icon: <ThunderboltOutlined className="text-amber-600" />,   title: title ?? "注意" },
    info: { bg: "bg-sky-50",     border: "border-sky-200",     icon: <StarOutlined className="text-sky-600" />,          title: title ?? "说明" },
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
   导航配置
   ============================================================ */

interface NavItem {
  id: string;
  label: string;
  icon: ReactNode;
}

const navItems: NavItem[] = [
  { id: "overview",       label: "编辑器概述",         icon: <HomeOutlined /> },
  { id: "task-manage",    label: "任务管理",           icon: <EditOutlined /> },
  { id: "flow-editor",    label: "流程编辑器",         icon: <BranchesOutlined /> },
  { id: "step-config",    label: "步骤配置面板",       icon: <ToolOutlined /> },
  { id: "layout-builder", label: "配置面板设计器",     icon: <BuildOutlined /> },
  { id: "variables",      label: "变量与参数",         icon: <ApartmentOutlined /> },
  { id: "common-steps",   label: "公共步骤",           icon: <ShareAltOutlined /> },
  { id: "subflows",       label: "子流程与监控",       icon: <EyeOutlined /> },
  { id: "shortcuts",      label: "快捷键与技巧",       icon: <ThunderboltOutlined /> },
  { id: "json-roundtrip", label: "与 JSON 协作",       icon: <CodeOutlined /> },
];

/* ============================================================
   主组件
   ============================================================ */

const EditorDocsPage: FC = () => {
  const contentRef = useRef<HTMLDivElement>(null);
  const [activeId, setActiveId] = useState("overview");

  const scrollTo = useCallback((id: string) => {
    const el = document.getElementById(id);
    if (el && contentRef.current) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, []);

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
    <div className="page-container !flex-row !p-0">
      {/* ======= 左侧导航 ======= */}
      <aside className="w-[220px] flex-shrink-0 border-r border-[var(--color-border)] flex flex-col bg-[var(--color-bg-container)]">
        <div className="flex items-center gap-2.5 px-5 py-4 border-b border-[var(--color-border)]">
          <span className="flex items-center justify-center w-7 h-7 rounded-lg bg-[#52c41a] text-white">
            <EditOutlined className="text-sm" />
          </span>
          <div>
            <Text strong className="text-[13px] text-[#1a1a2e] leading-tight block">编辑器教程</Text>
            <Text className="text-[10px] text-[#999] leading-tight">Editor Guide</Text>
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
                    ? "bg-[#f6ffed] text-[#52c41a] font-medium"
                    : "text-[#6b7280] hover:bg-[var(--color-bg-hover)] hover:text-[#1a1a2e]"
                  }
                `}
              >
                <span className={`text-sm flex-shrink-0 w-4 text-center ${isActive ? "text-[#52c41a]" : "text-[#bbb]"}`}>
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
              <span className="flex items-center justify-center w-9 h-9 rounded-xl bg-[#52c41a] shadow-md shadow-green-200">
                <EditOutlined className="text-lg text-white" />
              </span>
              <Title level={2} className="!mb-0 !text-[22px] !font-bold !tracking-tight">任务编辑器使用教程</Title>
            </div>
            <Paragraph className="!text-[#666] !text-[15px] !mb-0">
              可视化任务编辑器的完整使用指南。从新建任务到发布运行，逐步掌握每个功能模块。
            </Paragraph>
          </div>

          {/* 1. 编辑器概述 */}
          <Section id="overview" title="1. 编辑器概述">
            <Paragraph className="!text-[#444] !text-[14px]">
              任务编辑器是 Elves 提供的可视化任务创建工具。你不需要手写 JSON，通过拖拽连线和表单配置即可完成整个自动化流程的设计。
            </Paragraph>

            <Text strong className="text-[14px] block mb-2">界面布局</Text>
            <div className="bg-[#fafbfc] rounded-xl border border-[#e8eaed] p-5 font-mono text-[13px] leading-loose">
              {[
                ["左侧栏",  "任务列表 — 列出所有可用模板任务，点击切换编辑目标"],
                ["中央区",  "流程画布 — 以节点和连线展示步骤流转，支持拖拽和缩放"],
                ["右侧栏",  "步骤属性面板 — 编辑选中步骤的 action、params、跳转等"],
                ["底部栏",  "变量面板 / 设置面板 — 管理变量和 layout 配置项"],
              ].map(([zone, desc]) => (
                <div key={zone} className="flex items-start gap-3 mb-1.5">
                  <span className="text-[#52c41a] font-semibold w-16 flex-shrink-0">{zone}</span>
                  <span className="text-[#555]">{desc}</span>
                </div>
              ))}
            </div>
            <Callout type="info" title="两种方式协同">
              编辑器生成的最终产物与手写 JSON 格式完全一致。你可以在编辑器中可视化搭建，也可以直接编写 JSON——两者可以随时切换（编辑器内提供 JSON 预览模式）。
            </Callout>
          </Section>

          {/* 2. 任务管理 */}
          <Section id="task-manage" title="2. 任务管理">
            <Paragraph className="!text-[#444] !text-[14px]">
              进入编辑器后，首先看到左侧任务列表。
            </Paragraph>

            <Text strong className="text-[14px] block mb-2">新建任务</Text>
            <ol className="list-decimal pl-5 space-y-1 text-[13px] text-[#555]">
              <li>点击顶部 <strong>"新建任务"</strong> 按钮</li>
              <li>填写 <strong>任务名称</strong>（必填，需与文件夹名一致）和 <strong>版本号</strong>（必填，如 1.0.0）</li>
              <li>可选填写 <strong>作者</strong> 和 <strong>描述</strong></li>
              <li>确认后自动创建目录结构并进入编辑</li>
            </ol>

            <Divider className="!my-4" />
            <Text strong className="text-[14px] block mb-2">切换 / 搜索任务</Text>
            <Paragraph className="!text-[#666] !text-[13px]">
              在左侧搜索框输入任务名快速过滤。点击任务名称即可切换到对应任务编辑。
            </Paragraph>

            <Divider className="!my-4" />
            <Text strong className="text-[14px] block mb-2">保存</Text>
            <Paragraph className="!text-[#666] !text-[13px]">
              编辑器会检测未保存的修改，标题栏显示 <Tag color="orange" className="!text-[11px]">已修改</Tag> 标记。
              按 <InlineCode>Ctrl+S</InlineCode> 或点击工具栏保存按钮写入磁盘。
            </Paragraph>

            <Callout type="warn" title="自动恢复">
              编辑器支持草稿自动保存（localStorage）。若意外关闭，重新打开时会提示是否恢复未保存的修改。
            </Callout>
          </Section>

          {/* 3. 流程编辑器 */}
          <Section id="flow-editor" title="3. 流程编辑器（画布）">
            <Paragraph className="!text-[#444] !text-[14px]">
              流程编辑器是整个编辑器的核心。它以节点表示步骤，连线表示跳转关系。
            </Paragraph>

            <Text strong className="text-[14px] block mb-2">添加步骤节点</Text>
            <ol className="list-decimal pl-5 space-y-1 text-[13px] text-[#555]">
              <li>双击画布空白区域，弹出新建步骤对话框</li>
              <li>输入步骤名称，选择类型（普通步骤 / 公共步骤）</li>
              <li>确认后节点出现在画布上</li>
            </ol>

            <Divider className="!my-4" />
            <Text strong className="text-[14px] block mb-2">设置入口步骤（start）</Text>
            <Paragraph className="!text-[#666] !text-[13px]">
              在右侧属性面板的 "起始步骤" 下拉框中选择一个步骤作为任务入口点。
              被选中的步骤节点会显示特殊的绿色边框和图标。
            </Paragraph>

            <Divider className="!my-4" />
            <Text strong className="text-[14px] block mb-2">连线（控制流程）</Text>
            <Paragraph className="!text-[#666] !text-[13px]">
              从节点右侧的圆点拖拽连线到目标节点。每条连线有三种类型：
            </Paragraph>
            <div className="space-y-2 mb-3">
              {[
                { color: "#52c41a", label: "success（成功）",  desc: "action 返回非空结果时走此路径" },
                { color: "#ff4d4f", label: "failure（失败）",  desc: "action 返回空结果时走此路径" },
                { color: "#8b8fa3", label: "next（默认）",     desc: "无论成败，作为兜底跳转" },
              ].map(({ color, label, desc }) => (
                <div key={label} className="flex items-center gap-2 text-[13px]">
                  <span className="w-3 h-0.5 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
                  <span className="font-mono text-[12px]" style={{ color }}>{label}</span>
                  <span className="text-[#888]">{desc}</span>
                </div>
              ))}
            </div>

            <Divider className="!my-4" />
            <Text strong className="text-[14px] block mb-2">拖拽与画布操作</Text>
            <ul className="list-disc pl-5 space-y-1 text-[13px] text-[#555]">
              <li><strong>拖拽节点</strong> — 调整节点在画布上的位置（自动保存位置）</li>
              <li><strong>滚轮缩放</strong> — 放大 / 缩小画布</li>
              <li><strong>删除节点</strong> — 选中后按 <InlineCode>Delete</InlineCode> 键</li>
              <li><strong>右键菜单</strong> — 在节点上右键可快速编辑或删除</li>
              <li><strong>撤销 / 重做</strong> — <InlineCode>Ctrl+Z</InlineCode> / <InlineCode>Ctrl+Y</InlineCode></li>
            </ul>
          </Section>

          {/* 4. 步骤配置 */}
          <Section id="step-config" title="4. 步骤配置面板">
            <Paragraph className="!text-[#444] !text-[14px]">
              点击画布上的节点，右侧滑出步骤配置抽屉。可配置以下内容：
            </Paragraph>

            <Text strong className="text-[14px] block mb-2">基础信息</Text>
            <ul className="list-disc pl-5 space-y-1 text-[13px] text-[#555]">
              <li><InlineCode>action</InlineCode> — 选择动作类型（touch / exits / wait 等），支持自动补全</li>
              <li><InlineCode>description</InlineCode> — 步骤描述文本（仅注释，不影响运行）</li>
              <li><InlineCode>extends</InlineCode> — 继承另一个步骤的全部字段，父步骤支持自动补全</li>
            </ul>

            <Divider className="!my-4" />
            <Text strong className="text-[14px] block mb-2">params 参数</Text>
            <Paragraph className="!text-[#666] !text-[13px]">
              根据所选 action 类型，填写对应的参数。每个参数字段支持 <InlineCode>{"{变量}"}</InlineCode> 语法。
              点击右侧变量面板的标签可快速插入变量名到光标位置。
            </Paragraph>

            <Divider className="!my-4" />
            <Text strong className="text-[14px] block mb-2">流程控制</Text>
            <ul className="list-disc pl-5 space-y-1 text-[13px] text-[#555]">
              <li><InlineCode>success</InlineCode> / <InlineCode>failure</InlineCode> / <InlineCode>next</InlineCode> — 跳转目标，支持自动补全已有步骤名</li>
              <li><InlineCode>retry</InlineCode> — 失败重试次数和间隔(ms)</li>
              <li><InlineCode>prefix</InlineCode> / <InlineCode>postfix</InlineCode> — 步骤前后执行的子流程列表</li>
              <li><InlineCode>failure_extra</InlineCode> / <InlineCode>success_extra</InlineCode> — 失败/成功后额外执行的子流程</li>
              <li><InlineCode>set</InlineCode> — 步骤执行后更新变量</li>
            </ul>
          </Section>

          {/* 5. 配置面板设计器 */}
          <Section id="layout-builder" title="5. 配置面板设计器（Layout Builder）">
            <Paragraph className="!text-[#444] !text-[14px]">
              配置面板设计器用于设计任务的 <strong>运行时配置表单</strong>——即用户在 "任务管理" 页面配置参数值时看到的界面。
              它决定每个任务暴露哪些可调参数以及用什么控件编辑。
            </Paragraph>

            <Text strong className="text-[14px] block mb-2">基本概念</Text>
            <ul className="list-disc pl-5 space-y-1 text-[13px] text-[#555]">
              <li><strong>行（Row）</strong> — 表单的一行，可包含多个控件</li>
              <li><strong>控件（Cell）</strong> — 一个表单输入，如开关、输入框、下拉选择</li>
              <li><strong>store</strong> — 控件绑定的变量键名，对应 <InlineCode>values</InlineCode> 中的字段</li>
              <li><strong>span</strong> — 控件占用的栅格宽度（总共 24 格）</li>
            </ul>

            <Divider className="!my-4" />
            <Text strong className="text-[14px] block mb-2">操作流程</Text>
            <ol className="list-decimal pl-5 space-y-1 text-[13px] text-[#555]">
              <li>点击底部工具栏的 <strong>"设计配置面板"</strong> 进入 Layout 编辑器</li>
              <li>从左侧 <strong>"添加控件"</strong> 面板拖拽或点击控件类型到画布</li>
              <li>选中控件后，右侧面板编辑其属性：<InlineCode>store</InlineCode>（变量名）、<InlineCode>text</InlineCode>（标签）、<InlineCode>span</InlineCode>（宽度）等</li>
              <li>实时预览在下方，还原 "任务管理 → 配置" 的实际效果</li>
              <li>点击保存，Layout 写入任务 JSON</li>
            </ol>

            <Callout type="tip" title="store 命名建议">
              建议使用下划线命名法（如 <InlineCode>enable_auto_submit</InlineCode>、<InlineCode>max_retry</InlineCode>），
              避免与步骤中用到的运行时变量重名。
            </Callout>
          </Section>

          {/* 6. 变量与参数 */}
          <Section id="variables" title="6. 变量与参数">
            <Paragraph className="!text-[#444] !text-[14px]">
              变量是任务流程中的数据载体。通过变量可以实现计数、条件分支、动态参数等高级功能。
            </Paragraph>

            <Text strong className="text-[14px] block mb-2">变量的生命周期</Text>
            <div className="bg-[#fafbfc] rounded-xl border border-[#e8eaed] p-4 text-[13px]">
              <div className="flex items-center gap-2 mb-2">
                <Tag color="blue" className="!text-[10px]">初始值</Tag>
                <span className="text-[#555]">任务 JSON 的 <InlineCode>values</InlineCode> 字段定义，或通过配置面板修改</span>
              </div>
              <div className="flex items-center gap-2 mb-2">
                <Tag color="green" className="!text-[10px]">执行中</Tag>
                <span className="text-[#555]">步骤的 <InlineCode>set</InlineCode> 操作更新变量，后续步骤立即可用</span>
              </div>
              <div className="flex items-center gap-2">
                <Tag color="orange" className="!text-[10px]">子流程</Tag>
                <span className="text-[#555]">调用子流程时通过 <InlineCode>args</InlineCode> 传参合并到变量表</span>
              </div>
            </div>

            <Divider className="!my-4" />
            <Text strong className="text-[14px] block mb-2">在编辑器中操作变量</Text>
            <ul className="list-disc pl-5 space-y-1 text-[13px] text-[#555]">
              <li>右侧 <strong>变量面板</strong> 列出当前所有可用变量，点击可插入到输入框</li>
              <li>在步骤配置的 <InlineCode>set</InlineCode> 区域添加变量更新规则</li>
              <li>在 <InlineCode>params</InlineCode> 的任意文本中嵌入 <InlineCode>{"{变量名}"}</InlineCode></li>
              <li><InlineCode>{"{CONFIG.键名}"}</InlineCode> 引用全局设置页面的值</li>
            </ul>
          </Section>

          {/* 7. 公共步骤 */}
          <Section id="common-steps" title="7. 公共步骤">
            <Paragraph className="!text-[#444] !text-[14px]">
              公共步骤可以理解为 "步骤模板"，定义一次后在任务中多处复用，减少重复配置。
            </Paragraph>

            <Text strong className="text-[14px] block mb-2">添加公共步骤</Text>
            <Paragraph className="!text-[#666] !text-[13px]">
              添加节点时选择 <strong>"公共步骤"</strong> 类型（蓝色节点），它与普通步骤完全一样可以编辑，区别在于存储在 <InlineCode>common</InlineCode> 字段中。
            </Paragraph>

            <Divider className="!my-4" />
            <Text strong className="text-[14px] block mb-2">任务级 vs 全局级</Text>
            <ul className="list-disc pl-5 space-y-1 text-[13px] text-[#555]">
              <li><strong>任务级 common</strong> — 仅在当前任务内复用，定义在任务 JSON 的 <InlineCode>common</InlineCode> 字段</li>
              <li><strong>全局 common</strong> — 跨任务复用，定义在 <InlineCode>resources/config/common.json</InlineCode></li>
            </ul>
            <Callout type="info">
              任务级 common 的同名步骤会覆盖全局 common。编辑器中直接编辑的就是任务级 common。
            </Callout>
          </Section>

          {/* 8. 子流程与监控 */}
          <Section id="subflows" title="8. 子流程与监控器">
            <Text strong className="text-[14px] block mb-2">子流程</Text>
            <Paragraph className="!text-[#666] !text-[13px]">
              在步骤配置的 <InlineCode>prefix</InlineCode> / <InlineCode>postfix</InlineCode> 等字段中，可以引用其他步骤作为子流程执行。
              子流程列表中的每一项支持：
            </Paragraph>
            <ul className="list-disc pl-5 space-y-1 text-[13px] text-[#555]">
              <li><strong>纯步骤名</strong> — 简单引用一个步骤</li>
              <li><strong>步骤名*N</strong> — 重复执行 N 次（如 <InlineCode>点击*3</InlineCode>）</li>
              <li><strong>带参调用</strong> — 通过 <InlineCode>{"{step, args}"}</InlineCode> 格式传递参数</li>
              <li><strong>条件执行</strong> — 通过 <InlineCode>when</InlineCode> 字段控制是否执行</li>
            </ul>

            <Divider className="!my-4" />
            <Text strong className="text-[14px] block mb-2">监控器（Monitors）</Text>
            <Paragraph className="!text-[#666] !text-[13px]">
              在右侧属性面板底部可以配置后台监控：
            </Paragraph>
            <ul className="list-disc pl-5 space-y-1 text-[13px] text-[#555]">
              <li><InlineCode>loop</InlineCode> — 循环执行的步骤名列表</li>
              <li><InlineCode>interval</InlineCode> — 每轮循环的间隔秒数</li>
            </ul>
            <Paragraph className="!text-[#666] !text-[13px] mt-2">
              监控器在任务启动后以后台守护线程运行，主流程走到 "任务结束" 时自动停止。
            </Paragraph>
          </Section>

          {/* 9. 快捷键与技巧 */}
          <Section id="shortcuts" title="9. 快捷键与技巧">
            <div className="overflow-hidden rounded-xl border border-[#e8eaed]">
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="bg-[#f8f9fa] border-b border-[#e8eaed]">
                    <th className="text-left px-4 py-2.5 text-[#5f6368] text-[12px] font-semibold">操作</th>
                    <th className="text-left px-4 py-2.5 text-[#5f6368] text-[12px] font-semibold">快捷键</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    ["保存任务", "Ctrl + S"],
                    ["撤销", "Ctrl + Z"],
                    ["重做", "Ctrl + Y"],
                    ["删除选中节点", "Delete"],
                    ["新建步骤", "双击画布空白"],
                    ["画布缩放", "鼠标滚轮"],
                    ["节点右键菜单", "右键点击节点"],
                  ].map(([action, key]) => (
                    <tr key={action} className="border-b border-[#f0f0f0] last:border-none">
                      <td className="px-4 py-2 text-[#555]">{action}</td>
                      <td className="px-4 py-2">
                        <Tag className="!text-[11px] font-mono">{key}</Tag>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <Divider className="!my-5" />
            <Text strong className="text-[14px] block mb-2">实用技巧</Text>
            <ul className="list-disc pl-5 space-y-2 text-[13px] text-[#555]">
              <li><strong>先在纸上规划流程</strong> — 画布上连线多了容易乱。建议先在脑中理清步骤跳转关系，再用编辑器实现</li>
              <li><strong>善用 extends</strong> — 参数大部分相同的步骤，让一个 extends 另一个，改少量 params 即可</li>
              <li><strong>起好步骤名</strong> — 用描述性名称（如 "检查背包是否打开" 而不是 "步骤1"），方便在 prefix/success 等字段中识别</li>
              <li><strong>小步验证</strong> — 编辑部分步骤就保存并绑定窗口测试，不要一次性写完整个复杂流程再测</li>
              <li><strong>JSON 预览核对</strong> — 切换到 JSON 模式查看生成的 JSON 结构，确认逻辑无误</li>
            </ul>
          </Section>

          {/* 10. 与 JSON 协作 */}
          <Section id="json-roundtrip" title="10. 与手写 JSON 协作">
            <Paragraph className="!text-[#444] !text-[14px]">
              编辑器生成的 JSON 与手写格式完全兼容。你随时可以在两种方式间切换。
            </Paragraph>

            <Text strong className="text-[14px] block mb-2">从手写 JSON 迁移到编辑器</Text>
            <ol className="list-decimal pl-5 space-y-1 text-[13px] text-[#555]">
              <li>将手写的 JSON 放入正确的目录：<InlineCode>resources/config/任务名/版本号/任务名.json</InlineCode></li>
              <li>刷新页面或重启应用</li>
              <li>在编辑器左侧任务列表中找到该任务，点击即可编辑</li>
            </ol>

            <Divider className="!my-4" />
            <Text strong className="text-[14px] block mb-2">从编辑器导出 JSON 手动修改</Text>
            <ol className="list-decimal pl-5 space-y-1 text-[13px] text-[#555]">
              <li>编辑器中选择 JSON 预览模式查看当前 JSON</li>
              <li>直接编辑 <InlineCode>resources/config/任务名/版本号/任务名.json</InlineCode> 文件</li>
              <li>刷新编辑器，修改会自动反映到画布</li>
            </ol>

            <Callout type="warn">
              不要在编辑器打开的同时手动修改 JSON 文件——编辑器重新保存时会覆盖手动更改。
              建议先关闭该任务的编辑页面，修改 JSON，再重新打开。
            </Callout>
          </Section>

        </div>
      </div>
    </div>
  );
};

export default EditorDocsPage;
