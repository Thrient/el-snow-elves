"""OPPO JSBridge — 注入 HeytapNativeApi mock 到 WebView"""
import json
from .consts import GUID, PKG_HOST, build_vip_header_json

OPPO_CONSOLE_PREFIX = "__OPPO_NATIVE_INVOKE__::"


def _js_string_literal(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def build_mock_native_js() -> str:
    """生成注入到 WebView 的 HeytapNativeApi mock。"""

    vip_header_json = json.dumps(
        build_vip_header_json(), ensure_ascii=False, separators=(",", ":")
    )

    return f"""(function() {{
  if (window.HeytapNativeApi) return;

  const OPPO_CONSOLE_PREFIX = {_js_string_literal(OPPO_CONSOLE_PREFIX)};

  const PKG_ACCOUNT_SDK = "com.oplus.account.open.sdk";
  const PKG_HOST = {_js_string_literal(PKG_HOST)};
  const DEVICE_ID = "";
  const GUID = {_js_string_literal(GUID)};
  const APP_VERSION = 2012701;
  const APP_VERSION_STR = "2012701";
  const SSOID = "";
  const TOKEN = "";
  const BIZK = "3cd48b0c781835478b0a1783a9eff0c9";
  const APP_ID = "31288517";
  const PKG_NAME_SIGN = "00e7ec6745698936072925f64fc2a3e8";
  const DEVICE_MODEL = "MI";
  const DEVICE_ROM_BUILD = "V417IR";
  const DEVICE_TIME_ZONE = "Asia/Shanghai";
  const DEVICE_LOCALE = "zh_CN";
  const DEVICE_LANGUAGE = "zh";
  const DEVICE_LANGUAGE_TAG = "zh-CN";
  const DEVICE_COUNTRY = "CN";
  const DEVICE_COLOR_OS_VERSION = "0";

  const VIP_HEADER_JSON = {vip_header_json};

  function _emit(method, param, callbackid) {{
    try {{
      const payload = JSON.stringify({{
        method: method,
        param: param,
        callbackid: callbackid
      }});
      console.log(OPPO_CONSOLE_PREFIX + payload);
    }} catch (e) {{}}
  }}

  const methodResults = {{
    'accountExternalSdk.getSDKConfig': {{
      code: 0,
      msg: 'success!',
      data: {{
        bizk: BIZK,
        brand: 'other',
        business: PKG_HOST,
        country: 'CN',
        envInfo: JSON.stringify({{
          appId: APP_ID,
          deviceId: DEVICE_ID,
          envParam: "",
          pkgName: PKG_ACCOUNT_SDK,
          pkgNameSign: PKG_NAME_SIGN
        }})
      }}
    }},
    'vip.getClientContext': {{
      code: 0,
      msg: 'success!',
      data: {{
        ColorOsVersion: DEVICE_COLOR_OS_VERSION,
        GUID: GUID,
        appVersion: 0,
        buzRegion: '',
        deviceId: GUID,
        deviceRegion: DEVICE_COUNTRY,
        fromPackageName: PKG_HOST,
        isHTExp: false,
        language: DEVICE_LANGUAGE,
        languageTag: DEVICE_LANGUAGE_TAG,
        locale: DEVICE_LOCALE,
        model: DEVICE_MODEL,
        openId: GUID,
        packagename: PKG_HOST,
        payApkVersionCode: 0,
        romBuildDisplay: DEVICE_ROM_BUILD,
        timeZone: DEVICE_TIME_ZONE
      }}
    }},
    'account.getCurrentDomain': {{
      code: 0,
      msg: 'success!',
      data: {{ domain: 'https://uc-client-cn.heytapmobi.com' }}
    }},
    'vip.reportWebLog': {{ code: 0, msg: 'success!', data: {{}} }},
    'accountExternalSdk.getSupportThirdLoginTypes': {{
      code: 0,
      msg: 'success!',
      data: {{ loginTypes: '[]' }}
    }},
    'accountExternalSdk.isOpLogin': {{ code: 5999, msg: 'handleJsApi failed! exception', data: {{}} }},
    'account.getClientHeader': {{ code: 1, msg: 'unsupported operation!', data: {{}} }},
    'vip.getToken': {{
      code: 0,
      msg: 'success!',
      data: {{
        accountName: '',
        classifyByAge: '',
        country: '',
        ssoid: SSOID,
        ssoid_s: '',
        token: TOKEN,
        token_s: ''
      }}
    }},
    'vip.getHeaderJson': {{
      code: 0,
      msg: 'success!',
      data: VIP_HEADER_JSON
    }},
    'vip.setTitle': {{ code: 1, msg: 'unsupported operation!', data: {{}} }},
    'vip.setClientTitle': {{ code: 0, msg: 'success!', data: {{}} }}
  }};

  window.HeytapNativeApi = {{
    getNavBarType: function() {{ return 0; }},
    invoke: function(method, param, callbackid) {{
      _emit(method, param, callbackid);

      if (method === 'accountExternalSdk.setToken' || method === 'vip.onFinish') {{
        try {{
          var p = typeof param === 'string' ? JSON.parse(param) : param;
          window.__oppo_login_resp = (p && p.loginResp) ? p.loginResp : p;
        }} catch(e) {{}}
      }}

      if (method === 'account.CallMethodExecutor') {{
        window.__oppo_last_call_executor = param;
        window.__oppo_last_cme_callbackid = callbackid;
        return true;
      }}

      setTimeout(function() {{
        let result = methodResults[method];
        if (!result) {{
          result = {{ code: -1, msg: 'unknown method', data: {{}} }};
        }}
        const resultStr = JSON.stringify(result);
        if (window.HeytapJsApi && typeof window.HeytapJsApi.callback === 'function' && callbackid !== undefined && callbackid !== null) {{
          try {{
            window.HeytapJsApi.callback(callbackid.toString(), resultStr);
          }} catch (e) {{}}
        }}
      }}, 0);
      return true;
    }}
  }};
}})();
"""
