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

def get_db():
    return pymysql.connect(**_DB_CONFIG)


# ── 使用概览 ──────────────────────────────────────────────────────────────────

@router.get("/overview")
def overview():
    """总览卡片数据：总计算次数、AI占比、采纳率、平均节省费用"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # 计算次数按 session 去重（多方案类型共享同一 session_id，旧数据用 result_id 兜底）
            cur.execute("""
                SELECT
                  COUNT(DISTINCT COALESCE(session_id, result_id))                                    AS total_calcs,
                  COUNT(DISTINCT CASE WHEN ai_used=1 THEN COALESCE(session_id, result_id) END)       AS ai_calcs,
                  ROUND(AVG(utilization) * 100, 1)                                                    AS avg_utilization,
                  COUNT(DISTINCT CASE WHEN tier_upgraded=1 THEN COALESCE(session_id, result_id) END) AS tier_upgrade_count
                FROM pack_results
            """)
            _base = cur.fetchone()
            # 理论节省费用：每 session 只取最优方案的节省，避免多方案重复计算
            cur.execute("""
                SELECT ROUND(SUM(max_saving), 2) AS total_fee_saved
                FROM (
                  SELECT MAX(CASE WHEN fee_saved > 0 THEN fee_saved ELSE 0 END) AS max_saving
                  FROM pack_results
                  GROUP BY COALESCE(session_id, result_id)
                ) _s
            """)
            _fee = cur.fetchone()
            stats = {**_base, "total_fee_saved": _fee["total_fee_saved"]}

            cur.execute("""
                SELECT
                  COUNT(*)                                              AS total_feedback,
                  SUM(adopted = 1)                                     AS adopted_count,
                  ROUND(SUM(adopted=1) / COUNT(*) * 100, 1)            AS adoption_rate
                FROM feedback
                WHERE adopted IS NOT NULL
            """)
            fb = cur.fetchone()

            cur.execute("""
                SELECT
                  COALESCE(SUM(ai_input_tokens),  0) AS total_input_tokens,
                  COALESCE(SUM(ai_output_tokens), 0) AS total_output_tokens,
                  COALESCE(SUM(classify_input_tokens),  0) AS total_classify_input_tokens,
                  COALESCE(SUM(classify_output_tokens), 0) AS total_classify_output_tokens
                FROM pack_results
                WHERE ai_used = 1
            """)
            tok = cur.fetchone()

            # 实际节省费用：只统计 feedback.adopted=1 的记录
            cur.execute("""
                SELECT
                  ROUND(SUM(CASE WHEN pr.fee_saved > 0 THEN pr.fee_saved ELSE 0 END), 2) AS actual_fee_saved
                FROM pack_results pr
                LEFT JOIN feedback f ON f.result_id = pr.result_id
                WHERE f.adopted = 1
            """)
            actual_saved_row = cur.fetchone()

            # AI fallback 次数（ai_error IS NOT NULL）
            # 先检查 ai_error 列是否存在
            cur.execute("""
                SELECT COUNT(*) AS col_exists
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'pack_results'
                  AND COLUMN_NAME = 'ai_error'
            """)
            has_ai_error = cur.fetchone()["col_exists"] > 0
            if has_ai_error:
                cur.execute("SELECT SUM(ai_error IS NOT NULL) AS cnt FROM pack_results")
                ai_fallback_count = int(cur.fetchone()["cnt"] or 0)
            else:
                ai_fallback_count = 0

            # 近7天 vs 上7天 计算次数环比（按 session 去重）
            cur.execute("""
                SELECT
                  COUNT(DISTINCT CASE WHEN created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                    THEN COALESCE(session_id, result_id) END) AS this_week,
                  COUNT(DISTINCT CASE WHEN created_at >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
                    AND created_at < DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                    THEN COALESCE(session_id, result_id) END) AS last_week
                FROM pack_results
                WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
            """)
            week_calcs = cur.fetchone()

            # 近7天 vs 上7天 理论节省费用环比（每 session 只取最优方案节省）
            cur.execute("""
                SELECT
                  SUM(CASE WHEN wk=1 THEN max_saving ELSE 0 END) AS this_week,
                  SUM(CASE WHEN wk=0 THEN max_saving ELSE 0 END) AS last_week
                FROM (
                  SELECT
                    MAX(CASE WHEN fee_saved > 0 THEN fee_saved ELSE 0 END) AS max_saving,
                    MAX(CASE WHEN created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) THEN 1 ELSE 0 END) AS wk
                  FROM pack_results
                  WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
                  GROUP BY COALESCE(session_id, result_id)
                ) _sw
            """)
            week_saving = cur.fetchone()
    finally:
        conn.close()

    total_input  = int(tok["total_input_tokens"]  or 0)
    total_output = int(tok["total_output_tokens"] or 0)
    ai_cost      = round(total_input / 1_000_000 * 0.80 + total_output / 1_000_000 * 4.00, 6)

    classify_input  = int(tok["total_classify_input_tokens"]  or 0)
    classify_output = int(tok["total_classify_output_tokens"] or 0)
    classify_cost   = round(classify_input / 1_000_000 * 0.80 + classify_output / 1_000_000 * 4.00, 6)

    # 计算次数环比
    this_week_calcs = int(week_calcs["this_week"] or 0)
    last_week_calcs = int(week_calcs["last_week"] or 0)
    if last_week_calcs > 0:
        calcs_wow = round((this_week_calcs - last_week_calcs) / last_week_calcs * 100, 1)
    else:
        calcs_wow = None

    # 节省费用环比
    this_week_saving = float(week_saving["this_week"] or 0)
    last_week_saving = float(week_saving["last_week"] or 0)
    if last_week_saving > 0:
        saving_wow = round((this_week_saving - last_week_saving) / last_week_saving * 100, 1)
    else:
        saving_wow = None

    # AI ROI（分母含装箱推荐 + 防护分析两部分成本）
    actual_fee_saved = float(actual_saved_row["actual_fee_saved"] or 0)
    total_ai_cost = ai_cost + classify_cost
    if total_ai_cost > 0 and actual_fee_saved > 0:
        ai_roi = round(actual_fee_saved / total_ai_cost, 1)
    else:
        ai_roi = None

    total_calcs = int(stats["total_calcs"] or 0)
    ai_calcs    = int(stats["ai_calcs"]    or 0)
    ai_rate     = round(ai_calcs / total_calcs * 100, 1) if total_calcs > 0 else 0

    return {
        "total_calcs":         total_calcs,
        "ai_calcs":            ai_calcs,
        "ai_rate":             ai_rate,
        "avg_utilization":     stats["avg_utilization"] or 0,
        "total_fee_saved":     float(stats["total_fee_saved"] or 0),
        "tier_upgrade_count":  stats["tier_upgrade_count"] or 0,
        "total_feedback":      fb["total_feedback"] or 0,
        "adopted_count":       fb["adopted_count"] or 0,
        "adoption_rate":       fb["adoption_rate"] or 0,
        "total_input_tokens":       total_input,
        "total_output_tokens":      total_output,
        "ai_cost_usd":              ai_cost,
        "classify_input_tokens":    classify_input,
        "classify_output_tokens":   classify_output,
        "classify_cost_usd":        classify_cost,
        # 新增字段
        "actual_fee_saved":    actual_fee_saved,
        "ai_fallback_count":   ai_fallback_count,
        "this_week_calcs":     this_week_calcs,
        "last_week_calcs":     last_week_calcs,
        "calcs_wow":           calcs_wow,
        "this_week_saving":    round(this_week_saving, 2),
        "last_week_saving":    round(last_week_saving, 2),
        "saving_wow":          saving_wow,
        "ai_roi":              ai_roi,
    }


# ── 每日计算趋势 ──────────────────────────────────────────────────────────────

@router.get("/daily-trend")
def daily_trend(days: int = 30):
    """近 N 天每日计算次数 + AI 占比趋势"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                  DATE(created_at)                                                                       AS date,
                  COUNT(DISTINCT COALESCE(session_id, result_id))                                       AS total,
                  COUNT(DISTINCT CASE WHEN ai_used=1 THEN COALESCE(session_id, result_id) END)          AS ai_count
                FROM pack_results
                WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                GROUP BY DATE(created_at)
                ORDER BY date
            """, (days,))
            rows = cur.fetchall()
    finally:
        conn.close()
    return [{"date": str(r["date"]), "total": r["total"], "ai_count": int(r["ai_count"] or 0)} for r in rows]


# ── 方案类型分布 ──────────────────────────────────────────────────────────────

@router.get("/winner-distribution")
def winner_distribution():
    """推荐方案类型分布（rec/soft/best 各占比）"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT winner, COUNT(*) AS cnt
                FROM pack_results
                WHERE winner != ''
                GROUP BY winner
                ORDER BY cnt DESC
            """)
            rows = cur.fetchall()
    finally:
        conn.close()
    return [{"winner": r["winner"], "count": r["cnt"]} for r in rows]


# ── 采纳率分析 ────────────────────────────────────────────────────────────────

@router.get("/adoption-analysis")
def adoption_analysis():
    """按方案类型、选择方式分组的采纳率"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # 按方案类型
            cur.execute("""
                SELECT
                  selected_plan,
                  COUNT(*) AS total,
                  SUM(adopted = 1) AS adopted,
                  ROUND(SUM(adopted=1) / COUNT(*) * 100, 1) AS rate
                FROM feedback
                WHERE adopted IS NOT NULL AND selected_plan IS NOT NULL
                GROUP BY selected_plan
            """)
            by_plan = cur.fetchall()

            # 按选择方式
            cur.execute("""
                SELECT
                  selection_method,
                  COUNT(*) AS total,
                  SUM(adopted = 1) AS adopted,
                  ROUND(SUM(adopted=1) / COUNT(*) * 100, 1) AS rate
                FROM feedback
                WHERE adopted IS NOT NULL AND selection_method IS NOT NULL
                GROUP BY selection_method
            """)
            by_method = cur.fetchall()

            # 未采纳原因 TOP5
            cur.execute("""
                SELECT reason_changed, COUNT(*) AS cnt
                FROM feedback
                WHERE adopted = 0 AND reason_changed IS NOT NULL
                GROUP BY reason_changed
                ORDER BY cnt DESC
                LIMIT 5
            """)
            reasons = cur.fetchall()
    finally:
        conn.close()

    return {
        "by_plan":   [dict(r) for r in by_plan],
        "by_method": [dict(r) for r in by_method],
        "top_reasons": [dict(r) for r in reasons],
    }


# ── 效益量化 ──────────────────────────────────────────────────────────────────

@router.get("/benefit")
def benefit(days: int = 30):
    """效益量化：降档率、节省费用趋势"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # 费档分布
            cur.execute("""
                SELECT winner_tier, COUNT(*) AS cnt
                FROM pack_results
                WHERE winner_tier != ''
                GROUP BY winner_tier
                ORDER BY cnt DESC
            """)
            tier_dist = cur.fetchall()

            # 近 N 天每日节省费用
            cur.execute("""
                SELECT
                  DATE(created_at) AS date,
                  ROUND(SUM(CASE WHEN fee_saved > 0 THEN fee_saved ELSE 0 END), 2) AS saved,
                  SUM(tier_upgraded = 1) AS upgraded
                FROM pack_results
                WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                GROUP BY DATE(created_at)
                ORDER BY date
            """, (days,))
            daily_saving = cur.fetchall()

            # 利用率分布（按区间统计）
            cur.execute("""
                SELECT
                  CASE
                    WHEN utilization < 0.4  THEN '< 40%'
                    WHEN utilization < 0.6  THEN '40~60%'
                    WHEN utilization < 0.8  THEN '60~80%'
                    ELSE '≥ 80%'
                  END AS range_label,
                  COUNT(*) AS cnt
                FROM pack_results
                WHERE utilization IS NOT NULL
                GROUP BY range_label
            """)
            util_dist = cur.fetchall()

            cur.execute("""
                SELECT DATE(created_at)                       AS date,
                       COALESCE(SUM(ai_input_tokens),  0)    AS input_tokens,
                       COALESCE(SUM(ai_output_tokens), 0)    AS output_tokens
                FROM pack_results
                WHERE ai_used = 1
                  AND created_at >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                GROUP BY DATE(created_at)
                ORDER BY date
            """, (days,))
            token_daily = cur.fetchall()

            # 按 winner_bin 分组统计（全量，不受 days 影响）
            cur.execute("""
                SELECT
                  pr.winner_bin                                              AS bin,
                  COUNT(*)                                                   AS rec_count,
                  ROUND(SUM(CASE WHEN pr.fee_saved > 0 THEN pr.fee_saved ELSE 0 END), 2) AS theory_saving,
                  SUM(f.adopted = 1)                                         AS adopted_count,
                  COUNT(f.result_id)                                         AS feedback_count
                FROM pack_results pr
                LEFT JOIN feedback f ON f.result_id = pr.result_id
                WHERE pr.winner_bin IS NOT NULL AND pr.winner_bin != ''
                GROUP BY pr.winner_bin
                ORDER BY rec_count DESC
                LIMIT 15
            """)
            bin_rows = cur.fetchall()

            # 按 product_category 分组统计（全量，不受 days 影响）
            cur.execute("""
                SELECT
                  product_category                                            AS category,
                  COUNT(*)                                                    AS calc_count,
                  ROUND(SUM(CASE WHEN fee_saved > 0 THEN fee_saved ELSE 0 END), 2) AS theory_saving,
                  ROUND(AVG(utilization) * 100, 1)                           AS avg_utilization
                FROM pack_results
                WHERE product_category IS NOT NULL AND product_category != ''
                GROUP BY product_category
                ORDER BY theory_saving DESC
            """)
            cat_rows = cur.fetchall()
    finally:
        conn.close()

    # 处理 bin_stats：计算 adoption_rate
    bin_stats = []
    for r in bin_rows:
        feedback_count = int(r["feedback_count"] or 0)
        adopted_count  = int(r["adopted_count"] or 0)
        if feedback_count > 0:
            adoption_rate = round(adopted_count / feedback_count * 100, 1)
        else:
            adoption_rate = None
        bin_stats.append({
            "bin":            r["bin"],
            "rec_count":      int(r["rec_count"] or 0),
            "theory_saving":  float(r["theory_saving"] or 0),
            "adoption_rate":  adoption_rate,
            "feedback_count": feedback_count,
        })

    category_stats = [
        {
            "category":        r["category"],
            "calc_count":      int(r["calc_count"] or 0),
            "theory_saving":   float(r["theory_saving"] or 0),
            "avg_utilization": float(r["avg_utilization"] or 0),
        }
        for r in cat_rows
    ]

    return {
        "tier_distribution": [dict(r) for r in tier_dist],
        "daily_saving":      [{"date": str(r["date"]), "saved": float(r["saved"] or 0), "upgraded": int(r["upgraded"] or 0)} for r in daily_saving],
        "utilization_dist":  [dict(r) for r in util_dist],
        "token_daily":       [{"date": str(r["date"]), "input_tokens": int(r["input_tokens"] or 0), "output_tokens": int(r["output_tokens"] or 0)} for r in token_daily],
        # 新增字段
        "bin_stats":         bin_stats,
        "category_stats":    category_stats,
    }


# ── 计算结果明细 ───────────────────────────────────────────────────────────────

@router.get("/records")
def list_records(
    page: int = 1,
    page_size: int = 20,
    date_from: str = None,
    date_to: str = None,
    winner: str = None,
    ai_used: int = None,
    product_category: str = None,
):
    """分页查询计算结果明细"""
    conditions = []
    params = []

    if date_from:
        conditions.append("pr.created_at >= %s")
        params.append(date_from)
    if date_to:
        conditions.append("pr.created_at <= %s")
        params.append(date_to + " 23:59:59")
    if winner:
        conditions.append("pr.winner = %s")
        params.append(winner)
    if ai_used is not None:
        conditions.append("pr.ai_used = %s")
        params.append(ai_used)
    if product_category:
        conditions.append("pr.product_category = %s")
        params.append(product_category)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    offset = (page - 1) * page_size

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) AS total FROM pack_results pr {where}", params)
            total = cur.fetchone()["total"]

            cur.execute(f"""
                SELECT pr.result_id, pr.session_id, pr.calc_no, pr.plan_no, pr.plan_type,
                       pr.created_at, pr.product_category, pr.item_count,
                       ROUND(pr.total_weight, 3) AS total_weight,
                       pr.winner, pr.winner_bin, pr.winner_sku, pr.winner_tier,
                       CAST(pr.winner_total_fee AS CHAR) AS winner_total_fee,
                       pr.existing_bin, pr.existing_tier,
                       CAST(pr.existing_total_fee AS CHAR) AS existing_total_fee,
                       CAST(pr.fee_saved AS CHAR) AS fee_saved,
                       pr.tier_upgraded,
                       ROUND(pr.utilization * 100, 1) AS utilization_pct,
                       pr.ai_used, pr.ai_model, pr.ai_provider, pr.ai_input_tokens, pr.ai_output_tokens,
                       pr.classify_input_tokens, pr.classify_output_tokens,
                       pr.classify_source, pr.classify_model, pr.classify_provider,
                       sd.duration_ms,
                       pr.top3_existing_json
                FROM pack_results pr
                LEFT JOIN pack_scheme_detail sd ON sd.plan_no = pr.plan_no
                {where}
                ORDER BY pr.created_at DESC
                LIMIT %s OFFSET %s
            """, params + [page_size, offset])
            rows = cur.fetchall()
    finally:
        conn.close()

    return {"total": total, "page": page, "page_size": page_size, "rows": [dict(r) for r in rows]}


# ── 反馈情况明细 ───────────────────────────────────────────────────────────────

@router.get("/feedbacks")
def list_feedbacks(
    page: int = 1,
    page_size: int = 20,
    date_from: str = None,
    date_to: str = None,
    adopted: int = None,
    selected_plan: str = None,
):
    """分页查询反馈情况明细"""
    conditions = []
    params = []

    if date_from:
        conditions.append("created_at >= %s")
        params.append(date_from)
    if date_to:
        conditions.append("created_at <= %s")
        params.append(date_to + " 23:59:59")
    if adopted is not None:
        conditions.append("adopted = %s")
        params.append(adopted)
    if selected_plan:
        conditions.append("selected_plan = %s")
        params.append(selected_plan)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    offset = (page - 1) * page_size

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) AS total FROM feedback {where}", params)
            total = cur.fetchone()["total"]

            cur.execute(f"""
                SELECT result_id, session_id, calc_no, plan_no, plan_type, created_at, updated_at,
                       recommended_bin, recommended_sku,
                       selected_plan, selected_rank, selection_method,
                       adopted, actual_used_bin, actual_used_sku,
                       reason_changed, reason_detail, operator_id
                FROM feedback {where}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, params + [page_size, offset])
            rows = cur.fetchall()
    finally:
        conn.close()

    return {"total": total, "page": page, "page_size": page_size, "rows": [dict(r) for r in rows]}


# ── 数据来源（货品 + 自填包材）────────────────────────────────────────────────

@router.get("/records/{result_id}/source")
def record_source(result_id: str):
    """返回某次计算的输入货品明细和用户自填包材"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT item_id, length, width, height, weight, "
                "product_title, sale_price, product_category, soft_packaging_ok "
                "FROM pack_result_items WHERE result_id = %s",
                (result_id,),
            )
            items = cur.fetchall()

            cur.execute(
                "SELECT type, length, width, height, max_weight "
                "FROM pack_result_input_bins WHERE result_id = %s",
                (result_id,),
            )
            input_bins = cur.fetchall()
    finally:
        conn.close()

    return {"items": [dict(r) for r in items], "input_bins": [dict(r) for r in input_bins]}


# ── 方案明细存档（按 calc_no + plan_no 查询）─────────────────────────────────

@router.get("/scheme-detail")
def scheme_detail(calc_no: str, plan_no: str = None):
    """返回指定计算编号/方案编号的存档明细（AI文本、装箱结果、对比数据）"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            if plan_no:
                cur.execute(
                    "SELECT calc_no, plan_no, session_id, agent_summary, "
                    "final_result, compare_result, created_at "
                    "FROM pack_scheme_detail WHERE calc_no=%s AND plan_no=%s",
                    (calc_no, plan_no),
                )
                row = cur.fetchone()
                return dict(row) if row else {}
            else:
                cur.execute(
                    "SELECT calc_no, plan_no, session_id, agent_summary, "
                    "final_result, compare_result, created_at "
                    "FROM pack_scheme_detail WHERE calc_no=%s ORDER BY plan_no",
                    (calc_no,),
                )
                rows = cur.fetchall()
                return {"rows": [dict(r) for r in rows]}
    finally:
        conn.close()


# ── 筛选项枚举 ────────────────────────────────────────────────────────────────

@router.get("/filter-options")
def filter_options():
    """返回明细页筛选用的枚举值：产品分类、方案类型"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT product_category FROM pack_results WHERE product_category IS NOT NULL ORDER BY product_category")
            categories = [r["product_category"] for r in cur.fetchall()]

            cur.execute("SELECT DISTINCT winner FROM pack_results WHERE winner != '' AND winner IS NOT NULL ORDER BY winner")
            winners = [r["winner"] for r in cur.fetchall()]
    finally:
        conn.close()
    return {"categories": categories, "winners": winners}


# ── 优化反馈列表 ──────────────────────────────────────────────────────────────

@router.get("/optimization-feedbacks")
def optimization_feedbacks(
    page:      int = 1,
    page_size: int = 20,
    category:  str = "",
):
    """分页查询 optimization_feedback 表"""
    offset = (page - 1) * page_size
    conn = get_db()
    try:
        with conn.cursor() as cur:
            where = "WHERE 1=1"
            params = []
            if category:
                where += " AND category = %s"
                params.append(category)

            cur.execute(f"SELECT COUNT(*) AS cnt FROM optimization_feedback {where}", params)
            total = cur.fetchone()["cnt"]

            cur.execute(
                f"SELECT id, result_id, category, content, operator_id, created_at "
                f"FROM optimization_feedback {where} ORDER BY id DESC LIMIT %s OFFSET %s",
                params + [page_size, offset],
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return {"total": total, "items": [dict(r) for r in rows]}
