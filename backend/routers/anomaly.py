import sys
sys.stdout.reconfigure(encoding="utf-8")

import pymysql
import pymysql.cursors
from fastapi import APIRouter

router = APIRouter()

_DB_CONFIG = {
    "host":        "127.0.0.1",
    "port":        3306,
    "user":        "root",
    "password":    "Deng123456*",
    "database":    "packing_demo",
    "charset":     "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}

def _get_db():
    return pymysql.connect(**_DB_CONFIG)


@router.get("/stats")
def anomaly_stats(days: int = 7):
    """
    近 N 天异常汇总统计：
      - by_type: 各 anomaly_type × severity 计数
      - trend:   每日每类异常趋势
      - total:   近 N 天总数
      - today:   今日总数
    calc_timeout 只计单方案超时（排除 scope=session 的 session 级汇总记录）
    """
    conn = _get_db()
    try:
        with conn.cursor() as cur:
            # 各类型计数（calc_timeout 排除 session 级）
            cur.execute("""
                SELECT anomaly_type, severity, COUNT(*) AS cnt
                FROM anomaly_log
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                  AND NOT (anomaly_type = 'calc_timeout'
                           AND JSON_UNQUOTE(JSON_EXTRACT(extra, '$.scope')) = 'session')
                GROUP BY anomaly_type, severity
                ORDER BY cnt DESC
            """, (days,))
            by_type = cur.fetchall()

            # 每日趋势（同样排除 session 级超时）
            cur.execute("""
                SELECT DATE(created_at) AS day, anomaly_type, COUNT(*) AS cnt
                FROM anomaly_log
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                  AND NOT (anomaly_type = 'calc_timeout'
                           AND JSON_UNQUOTE(JSON_EXTRACT(extra, '$.scope')) = 'session')
                GROUP BY day, anomaly_type
                ORDER BY day
            """, (days,))
            trend_rows = cur.fetchall()
            for r in trend_rows:
                if r.get("day"):
                    r["day"] = r["day"].strftime("%m-%d")

            # 总数 & 今日数（同样排除 session 级超时）
            cur.execute("""
                SELECT
                  COUNT(*) AS total,
                  SUM(DATE(created_at) = CURDATE()) AS today
                FROM anomaly_log
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                  AND NOT (anomaly_type = 'calc_timeout'
                           AND JSON_UNQUOTE(JSON_EXTRACT(extra, '$.scope')) = 'session')
            """, (days,))
            counts = cur.fetchone()

        return {
            "by_type": by_type,
            "trend":   trend_rows,
            "total":   counts["total"] or 0,
            "today":   counts["today"] or 0,
        }
    finally:
        conn.close()


@router.get("/list")
def list_anomalies(
    page:         int = 1,
    page_size:    int = 20,
    anomaly_type: str = None,
    severity:     str = None,
    date_start:   str = None,
    date_end:     str = None,
):
    """分页查询异常明细，支持按类型、严重程度、时间区间过滤"""
    conn = _get_db()
    try:
        with conn.cursor() as cur:
            where  = ["1=1"]
            params = []
            if anomaly_type:
                where.append("anomaly_type=%s"); params.append(anomaly_type)
            if severity:
                where.append("severity=%s"); params.append(severity)
            if date_start:
                where.append("created_at>=%s"); params.append(date_start + " 00:00:00")
            if date_end:
                where.append("created_at<=%s"); params.append(date_end + " 23:59:59")

            w = " AND ".join(where)
            cur.execute(f"SELECT COUNT(*) AS total FROM anomaly_log WHERE {w}", params)
            total = (cur.fetchone() or {}).get("total", 0)

            offset = (page - 1) * page_size
            cur.execute(f"""
                SELECT id, created_at, anomaly_type, severity, session_id, calc_no,
                       error_code, error_msg, duration_ms, extra,
                       JSON_UNQUOTE(JSON_EXTRACT(extra, '$.scope')) AS scope
                FROM anomaly_log WHERE {w}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, params + [page_size, offset])
            rows = cur.fetchall()

            for r in rows:
                if r.get("created_at"):
                    r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M:%S")

        return {"total": total, "rows": rows}
    finally:
        conn.close()
