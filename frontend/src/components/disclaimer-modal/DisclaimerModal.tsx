import { Modal, Checkbox, Button, Typography, Divider } from 'antd'
import { useState } from 'react'
import { useSysStore } from '@/store/sys-store'

const { Title, Paragraph, Text } = Typography

const SECTION = ({ n, title, children }: { n: number; title: string; children: React.ReactNode }) => (
  <div className="flex flex-col gap-1.5">
    <div className="flex items-center gap-2">
      <span className="w-6 h-6 rounded-lg bg-slate-100 text-[11px] font-bold text-slate-500 flex items-center justify-center shrink-0">{n}</span>
      <Text strong className="text-[13px]">{title}</Text>
    </div>
    <div className="pl-8 text-[12px] leading-relaxed text-slate-600">{children}</div>
  </div>
)

export default function DisclaimerModal() {
  const [checked, setChecked] = useState(false)
  const disclaimerAccepted = useSysStore((s) => s.disclaimerAccepted)
  const acceptDisclaimer = useSysStore((s) => s.acceptDisclaimer)

  return (
    <Modal
      open={!disclaimerAccepted}
      closable={false}
      mask={{ closable: false }}
      keyboard={false}
      footer={null}
      width={620}
      centered
    >
      <div className="flex flex-col gap-4 py-2">
        <div className="text-center">
          <Title level={3} className="!mb-1 !text-[#1a1a2e]">用户协议与免责声明</Title>
          <Text type="secondary" className="text-[12px]">在使用本工具之前，请仔细阅读以下条款</Text>
        </div>

        <Divider className="!my-0" />

        <div className="flex flex-col gap-4 max-h-[360px] overflow-y-auto pr-2">
          <SECTION n={1} title="工具性质与目的">
            本工具（<Text strong>时雪</Text>）是一款面向个人用户的<Text strong>游戏辅助工具</Text>，
            通过计算机视觉（CV）和输入模拟技术实现游戏操作的自动化。
            本工具<Text strong>不修改</Text>游戏客户端内存、<Text strong>不解包</Text>游戏资源、
            <Text strong>不破解</Text>游戏加密协议。所有操作均在操作系统层面模拟用户行为，
            类似于按键精灵、AutoHotkey 等自动化软件。
          </SECTION>

          <SECTION n={2} title="学习与研究目的">
            本工具仅供<Text strong>个人学习、研究和技术交流</Text>。用户通过本工具
            可直接接触到 Python 脚本编程、React 前端开发、计算机视觉（OpenCV）、
            HTTP 代理（mitmproxy）等真实技术场景，在提升游戏效率的同时加深对
            编程和自动化的理解。
          </SECTION>

          <SECTION n={3} title="游戏合规性">
            使用本工具<Text strong>可能违反</Text>相关游戏的用户协议或服务条款。
            部分游戏明确禁止任何形式的自动化脚本或第三方辅助工具。
            使用者应<Text strong>自行查阅并确认</Text>目标游戏的相关规定。
            因违反游戏规则而产生的一切后果（包括但不限于账号警告、临时封禁、
            永久封禁、数据清除、虚拟财产损失等），<Text strong>均由使用者自行承担</Text>，
            开发者不承担任何责任。
          </SECTION>

          <SECTION n={4} title="账号安全与隐私">
            本工具所有数据（包括但不限于任务配置、账号凭证、模板图片等）均存储于
            用户<Text strong>本地设备</Text>。账号凭证使用 AES-256-GCM 加密，
            密钥与设备硬件绑定。本工具<Text strong>不会</Text>收集、上传或泄露
            用户的任何个人信息、游戏账号或密码。使用者应自行保管好自己的设备
            和数据文件。
          </SECTION>

          <SECTION n={5} title="技术要求与合法使用">
            本工具中包含的网络流量分析功能（HTTP 代理）基于开源的 mitmproxy 框架实现，
            DNS 劫持通过修改本机 hosts 文件实现。以上技术手段仅作用于<Text strong>用户自己的设备</Text>，
            不涉及对他人服务器或网络设备的攻击、入侵或干扰。使用者<Text strong>严禁</Text>将本工具
            用于以下目的：
            <ul className="m-0 mt-1 flex flex-col gap-0.5 list-disc pl-5">
              <li>攻击、破坏或干扰任何网络服务</li>
              <li>非法获取他人账号或信息</li>
              <li>任何违反《中华人民共和国网络安全法》《中华人民共和国计算机信息系统安全保护条例》的行为</li>
              <li>商业盈利性质的批量账号操作</li>
            </ul>
          </SECTION>

          <SECTION n={6} title="第三方开源组件">
            本工具使用了多个开源组件（包括但不限于 mitmproxy、OpenCV、React、Ant Design 等），
            各组件遵循其各自的许可证条款。使用者应知晓这些组件的存在并尊重其知识产权。
          </SECTION>

          <SECTION n={7} title="无担保声明">
            本工具按<Text strong>"现状"</Text>提供，不提供任何形式的明示或默示担保，
            包括但不限于适销性、特定用途适用性及不侵权的担保。开发者<Text strong>不保证</Text>：
            <ul className="m-0 mt-1 flex flex-col gap-0.5 list-disc pl-5">
              <li>工具功能完全满足使用者的需求</li>
              <li>工具运行不受中断、完全无错或安全可靠</li>
              <li>工具缺陷会被修复</li>
              <li>工具能持续适配游戏版本更新</li>
            </ul>
          </SECTION>

          <SECTION n={8} title="责任限制">
            在任何情况下，包括但不限于疏忽，开发者均<Text strong>不对</Text>因使用
            或无法使用本工具所造成的任何直接、间接、偶然、特殊、惩罚性或后果性损害
            （包括但不限于：游戏账号损失、数据丢失、设备损坏、业务中断、商誉损失、
            利润损失及其他经济损失）承担责任，即使开发者已被告知此类损害的可能性。
          </SECTION>
        </div>

        <Divider className="!my-0" />

        <div className="flex flex-col gap-3">
          <Paragraph className="!mb-0 text-[12px] text-[#ef4444] leading-relaxed font-medium">
            继续使用即表示您确认已阅读、理解并同意上述全部条款。
            如您不同意任一条款，请关闭本工具。
          </Paragraph>

          <Checkbox
            checked={checked}
            onChange={(e) => setChecked(e.target.checked)}
            className="text-[13px]"
          >
            <span className="text-slate-700">我已充分阅读、理解并同意上述全部条款</span>
          </Checkbox>

          <Button
            type="primary"
            block
            size="large"
            disabled={!checked}
            onClick={acceptDisclaimer}
            className="!rounded-xl !h-11 !text-[14px]"
          >
            同意并继续
          </Button>
        </div>
      </div>
    </Modal>
  )
}
