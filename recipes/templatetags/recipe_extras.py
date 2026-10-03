import re

from django import template

register = template.Library()

# Leading amount such as "1,5", "1/2", "2-3" or "½", optionally followed by a unit.
_AMOUNT = r"(?:\d+(?:[.,]\d+)?(?:\s*[-–/]\s*\d+(?:[.,]\d+)?)?|[½¼¾⅓⅔])"
_UNITS = (
    "kg|hg|g|l|dl|cl|ml|msk|tsk|krm|st|förp|paket|pkt|burk|burkar|påse|påsar|"
    "kvist|kvistar|klyfta|klyftor|skiva|skivor|nypa|knippe|bunt"
)
_QUANTITY = re.compile(rf"^\s*({_AMOUNT}(?:\s+(?:{_UNITS})\.?)?)\s+(.+)$", re.IGNORECASE)


@register.filter
def split_quantity(line):
    """Split "1,5 kg lammstek" into ("1,5 kg", "lammstek"); lines without an amount give ("", line)."""
    match = _QUANTITY.match(line)
    if not match:
        return "", line.strip()
    return match.group(1), match.group(2).strip()
