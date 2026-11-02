"""Route a small set of product questions before the SQL workflow."""

import re


CAPABILITIES_ANSWER = (
    "我可以查询当前演示库中的订单数据：订单数、销量、销售额、GMV 和平均订单金额；"
    "也可以按商品、品类、品牌、地区、客户会员等级和日期做筛选、分组、排行。"
    "例如：‘查询订单总数’、‘统计华东地区销售额最高的三个商品’。"
    "当前数据是演示数据，主要覆盖 2025 年 1 月至 3 月。"
    "我暂时不能查询库外的实时业务数据，也不支持通用闲聊。"
)

_CAPABILITIES_QUESTIONS = re.compile(
    r"^(?:你|这个(?:系统|项目|助手)|大衍)?"
    r"(?:能|可以|能够|会|支持)?"
    r"(?:提供|做|查|查询|回答|分析|处理|实现)?"
    r"(?:哪些|什么|啥|哪几种)?"
    r"(?:能力|功能|问题|数据|分析)(?:呢|呀|啊|吗)?$"
)
_DIRECT_QUESTIONS = {
    "你能做什么", "你会做什么", "你能查什么", "你支持什么",
    "你有哪些功能", "你有哪些能力", "有哪些功能", "有哪些能力",
    "能提供哪些能力", "能做什么", "可以做什么", "能查什么数据",
    "支持哪些问题", "这个项目能做什么", "这个系统能做什么",
}


def get_direct_answer(query: str) -> str | None:
    normalized = re.sub(r"[\s，,。？！?!：:]+", "", query).strip()
    if normalized in _DIRECT_QUESTIONS or _CAPABILITIES_QUESTIONS.fullmatch(normalized):
        return CAPABILITIES_ANSWER
    return None
