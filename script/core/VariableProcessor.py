import json
import re
import ast
import operator
from abc import ABC, abstractmethod


# ---------- 安全表达式求值器 ----------
_EXPR_CACHE = {}


class SafeExpressionEvaluator:
    """安全求值 AST 表达式，仅允许常量、变量、基本算术和比较运算。"""
    _BIN_OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }
    _UNARY_OPS = {
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
        ast.Not: operator.not_,
    }

    def __init__(self, variables, computed=None):
        self.variables = variables
        self.computed = computed or {}

    def evaluate(self, expr):
        if expr in _EXPR_CACHE:
            return self._eval_node(_EXPR_CACHE[expr].body)

        try:
            tree = ast.parse(expr, mode='eval')
        except SyntaxError as e:
            raise ValueError("表达式语法错误: {}".format(expr)) from e

        # 验证节点安全性（不依赖 NodeVisitor）
        self._validate_node(tree.body)
        _EXPR_CACHE[expr] = tree
        # 求值
        return self._eval_node(tree.body)

    def _validate_node(self, node):
        """递归验证节点是否安全（仅允许白名单节点类型）"""
        allowed_types = (
            ast.Constant, ast.Name, ast.BinOp, ast.UnaryOp, ast.Compare,
            ast.BoolOp, ast.Subscript, ast.Attribute, ast.Call,
            ast.Load, ast.Store,
            ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
            ast.USub, ast.UAdd, ast.Not,
            ast.And, ast.Or,
            ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
        )
        if not isinstance(node, allowed_types):
            raise ValueError("表达式中包含不安全的节点类型: {}".format(type(node).__name__))

        # 递归检查子节点
        for child in ast.iter_child_nodes(node):
            self._validate_node(child)

    def _eval_node(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id == "True":
                return True
            if node.id == "False":
                return False
            if node.id == "None":
                return None
            if node.id in self.variables:
                return self.variables[node.id]
            if node.id in self.computed:
                return self.computed[node.id]()
            raise NameError("未定义变量: {}".format(node.id))
        if isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_type = type(node.op)
            if op_type in self._BIN_OPS:
                return self._BIN_OPS[op_type](left, right)
            raise TypeError("不支持的二元运算符: {}".format(op_type.__name__))
        if isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op_type = type(node.op)
            if op_type in self._UNARY_OPS:
                return self._UNARY_OPS[op_type](operand)
            raise TypeError("不支持的一元运算符: {}".format(op_type.__name__))
        if isinstance(node, ast.Compare):
            left = self._eval_node(node.left)
            for op, right_node in zip(node.ops, node.comparators):
                right = self._eval_node(right_node)
                if isinstance(op, ast.Eq):
                    if left != right:
                        return False
                elif isinstance(op, ast.NotEq):
                    if left == right:
                        return False
                elif isinstance(op, ast.Lt):
                    if not left < right:
                        return False
                elif isinstance(op, ast.LtE):
                    if not left <= right:
                        return False
                elif isinstance(op, ast.Gt):
                    if not left > right:
                        return False
                elif isinstance(op, ast.GtE):
                    if not left >= right:
                        return False
                else:
                    raise TypeError("不支持的比较运算符: {}".format(type(op).__name__))
                left = right
            return True

        if isinstance(node, ast.BoolOp):
            values = [self._eval_node(v) for v in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            if isinstance(node.op, ast.Or):
                return any(values)
            raise TypeError("不支持的布尔运算符: {}".format(type(node.op).__name__))

        # 新增：下标访问（列表、元组、字符串、字典）
        if isinstance(node, ast.Subscript):
            obj = self._eval_node(node.value)
            idx = self._eval_node(node.slice)
            if isinstance(obj, (list, tuple, str)):
                if not isinstance(idx, int):
                    raise TypeError("列表/字符串索引必须为整数")
                return obj[idx]
            elif isinstance(obj, dict):
                return obj[idx]
            else:
                raise TypeError(f"不支持下标访问的类型: {type(obj)}")

        # 新增：属性访问（仅支持字典的键访问，如 dict.key）
        if isinstance(node, ast.Attribute):
            obj = self._eval_node(node.value)
            if isinstance(obj, dict):
                return obj[node.attr]
            raise TypeError(f"不支持属性访问，对象类型: {type(obj)}")

        # 新增：函数调用（仅允许 len()、split() 和 choice()）
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and not node.keywords:
                args = [self._eval_node(a) for a in node.args]
                if node.func.id == 'len' and len(args) == 1:
                    return len(args[0])
                if node.func.id == 'split' and len(args) == 2:
                    return str(args[0]).split(str(args[1]))
                if node.func.id == 'choice' and len(args) == 1:
                    import random
                    return random.choice(list(args[0]))
            raise TypeError("仅支持 len()、split() 和 choice() 函数调用")

        raise TypeError("不支持的 AST 节点类型: {}".format(type(node).__name__))


# ---------- 可求值对象抽象 ----------
class Evaluable(ABC):
    @abstractmethod
    def evaluate(self, result, variables):
        pass


class ConstantValue(Evaluable):
    def __init__(self, value):
        self.value = value

    def evaluate(self, result, variables, computed=None):
        return self.value


class ResultPlaceholder(Evaluable):
    def evaluate(self, result, variables, computed=None):
        return result


class ExpressionValue(Evaluable):
    def __init__(self, expr_template, var_names):
        self.expr_template = expr_template
        self.var_names = var_names

    def evaluate(self, result, variables, computed=None):
        evaluator = SafeExpressionEvaluator({**variables, "result": result}, computed)
        return evaluator.evaluate(self.expr_template)


class AutoIncrementDecrement(Evaluable):
    def __init__(self, var_name, delta):
        self.var_name = var_name
        self.delta = delta

    def evaluate(self, result, variables, computed=None):
        if self.var_name not in variables:
            raise NameError("未定义变量: {}".format(self.var_name))
        current = variables[self.var_name]
        if not isinstance(current, (int, float)):
            raise TypeError("变量 {} 不是数值类型，无法自增/自减".format(self.var_name))
        return current + self.delta


# ---------- 值解析器接口 ----------
class ValueParser(ABC):
    @abstractmethod
    def parse(self, raw_value):
        pass


class ConstantParser(ValueParser):
    def parse(self, raw_value):
        if not isinstance(raw_value, str):
            return ConstantValue(raw_value)
        return None


class ResultPlaceholderParser(ValueParser):
    def parse(self, raw_value):
        if isinstance(raw_value, str) and raw_value.strip() == "{result}":
            return ResultPlaceholder()
        return None


class AutoIncrementDecrementParser(ValueParser):
    _PATTERN = re.compile(r'^\{(\w+)}\+\+$|^\{(\w+)}--$')

    def parse(self, raw_value):
        if not isinstance(raw_value, str):
            return None
        match = self._PATTERN.match(raw_value.strip())
        if not match:
            return None
        inc_var = match.group(1)
        dec_var = match.group(2)
        if inc_var:
            return AutoIncrementDecrement(inc_var, +1)
        else:
            return AutoIncrementDecrement(dec_var, -1)


class ExpressionParser(ValueParser):
    _VAR_PATTERN = re.compile(r'\{([^{}:]+)}')

    def parse(self, raw_value):
        if not isinstance(raw_value, str):
            return None
        if '{' not in raw_value and '}' not in raw_value:
            return None
        var_names = self._VAR_PATTERN.findall(raw_value)
        if not var_names:
            return None

        def replacer(match):
            return match.group(1)

        expr_str = self._VAR_PATTERN.sub(replacer, raw_value)
        return ExpressionValue(expr_str, var_names)


class DefaultValue(Evaluable):
    def __init__(self, var_name, default_value):
        self.var_name = var_name
        self.default_value = default_value

    def evaluate(self, result, variables, computed=None):
        if computed and self.var_name in computed:
            return computed[self.var_name](self.default_value)
        return variables.get(self.var_name, self.default_value)


class DefaultValueParser(ValueParser):
    """处理 {变量:默认值} 语法，变量不存在时使用默认值"""
    _PATTERN = re.compile(r'^\{([^{}:]+):(.+)}$', re.DOTALL)

    def parse(self, raw_value):
        if not isinstance(raw_value, str):
            return None
        match = self._PATTERN.match(raw_value.strip())
        if not match:
            return None
        var_name = match.group(1)
        default_str = match.group(2)
        try:
            default_value = json.loads(default_str)
        except (json.JSONDecodeError, ValueError):
            default_value = default_str
        return DefaultValue(var_name, default_value)


class InlineTemplateParser(ValueParser):
    """处理字符串内嵌的 {变量:默认值}，如 '按钮地图{目标区域:江南}区域'
       仅匹配带 : 的模板，避免拦截 {Escape} 等表达式"""
    _TEMPLATE_RE = re.compile(r'\{([^{}:]+):([^}]*)\}')

    def parse(self, raw_value):
        if not isinstance(raw_value, str):
            return None
        if '{' not in raw_value or ':' not in raw_value:
            return None
        matches = self._TEMPLATE_RE.findall(raw_value)
        if not matches:
            return None
        return InlineTemplateValue(raw_value, matches)


class InlineTemplateValue(Evaluable):
    def __init__(self, template, matches):
        self.template = template
        self.matches = matches

    def evaluate(self, result, variables, computed=None):
        def replacer(m):
            var_name = m.group(1)
            default = m.group(2)
            if computed and var_name in computed:
                return str(computed[var_name](default))
            return str(variables.get(var_name, default))
        return InlineTemplateParser._TEMPLATE_RE.sub(replacer, self.template)


class BraceExpressionParser(ValueParser):
    """处理整个字符串被 {expr} 包裹的纯表达式，如 {a + b > 5}"""
    _PATTERN = re.compile(r'^\{(.+)}$', re.DOTALL)

    def parse(self, raw_value):
        if not isinstance(raw_value, str):
            return None
        match = self._PATTERN.match(raw_value.strip())
        if not match:
            return None
        return ExpressionValue(match.group(1), [])


class JsonParser(ValueParser):
    """尝试将字符串反序列化为 Python 对象（数字/布尔/列表/字典）"""
    def parse(self, raw_value):
        if not isinstance(raw_value, str):
            return None
        try:
            return ConstantValue(json.loads(raw_value.strip()))
        except (json.JSONDecodeError, ValueError):
            return None


# ---------- 类型转换 ----------

_VTYPE_COERCE = {
    "text": lambda v: str(v) if not isinstance(v, str) else v,
    "number": lambda v: float(v) if '.' in str(v) else int(v),
    "bool": lambda v: v if isinstance(v, bool) else str(v).lower() in ("true", "1", "yes"),
    "list": lambda v: json.loads(v) if isinstance(v, str) and v.strip().startswith('[') else (list(v) if isinstance(v, (list, tuple)) else [v]),
}


# ---------- 变量处理器 ----------
class VariableProcessor:
    def __init__(self, variables=None, value_types=None):
        self.variables = variables or dict()
        self._value_types = value_types or {}
        self._computed = {}
        self._parsers = []
        self._lock = __import__('threading').Lock()
        self._register_default_parsers()
        if value_types:
            self._apply_type_hints(value_types)

    def _apply_type_hints(self, value_types):
        """统一入口：按声明的类型转换所有变量"""
        for name, vtype in value_types.items():
            if name in self.variables and vtype in _VTYPE_COERCE:
                try:
                    self.variables[name] = _VTYPE_COERCE[vtype](self.variables[name])
                except Exception:
                    pass  # 转换失败保持原值

    def _coerce_value(self, name, value):
        """对 set 操作的结果按已声明类型转换"""
        vtype = getattr(self, '_value_types', {}).get(name)
        if vtype and vtype in _VTYPE_COERCE:
            try:
                return _VTYPE_COERCE[vtype](value)
            except Exception:
                pass
        return value

    def _register_default_parsers(self):
        self._parsers.append(ConstantParser())
        self._parsers.append(ResultPlaceholderParser())
        self._parsers.append(AutoIncrementDecrementParser())
        self._parsers.append(DefaultValueParser())
        self._parsers.append(InlineTemplateParser())
        self._parsers.append(BraceExpressionParser())
        self._parsers.append(ExpressionParser())
        self._parsers.append(JsonParser())

    def register_parser(self, parser):
        self._parsers.append(parser)

    def register_computed(self, name, fn):
        self._computed[name] = fn

    def process_value(self, raw_value, result):
        for parser in self._parsers:
            evaluable = parser.parse(raw_value)
            if evaluable is not None:
                try:
                    return evaluable.evaluate(result, self.variables, self._computed)
                except Exception as e:
                    raise ValueError("求值失败: {} -> {}".format(raw_value, e)) from e
        return raw_value

    def apply_set(self, op, result):
        if 'set' not in op:
            return
        with self._lock:
            for item in op['set']:
                name = item['name']
                raw_value = item['value']
                final_value = self.process_value(raw_value, result)
                self.variables[name] = self._coerce_value(name, final_value)

    def bulk_update(self, args):
        with self._lock:
            self.variables.update(args)
