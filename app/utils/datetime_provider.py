from flask.json.provider import DefaultJSONProvider
from datetime import datetime, timezone, timedelta

BJ_TZ = timezone(timedelta(hours=8))

def datetime_to_bj(dt):
    """把数据库中的 datetime(UTC) 转成北京时间字符串"""
    if dt is None:
        return None

    # 老数据可能没有 tzinfo → 按 UTC 处理
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    bj = dt.astimezone(BJ_TZ)
    return bj.strftime("%Y-%m-%d %H:%M:%S")


class BJJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, datetime):
            return datetime_to_bj(obj)
        return super().default(obj)
