from datetime import datetime, timedelta

# --------------------------
# 全局自适应系数（核心创新）自适应强度，根据近7天推送频率计算
# --------------------------
def adaptive_intensity(weekly_push_count):
    # 近7天推送总数
    intensity = min(weekly_push_count / 7, 5)  # 强度上限 5
    return intensity

# --------------------------
# 1. 自适应新鲜度，新语录权重更高
# --------------------------
def fresh_factor(create_time, now, intensity):
    delta = now - create_time
    day = delta.days
    
    if day == 0:
        return 2.0 / (intensity * 0.3 + 1)
    elif day <= 3:
        return 1.5 / (intensity * 0.2 + 1)
    elif day <= 7:
        return 1.2
    return 1.0

# --------------------------
# 2. 自适应冷却，刚推送过的语录被冷却
# --------------------------
def cool_factor(last_push, now, intensity):
    if not last_push:
        return 1.0
    hours = (now - last_push).total_seconds() / 3600
    if hours < 4:
        return 0.05
    elif hours < 12:
        return 0.2
    elif intensity > 0 and hours < 24 * (1 / intensity):
        return 0.6
    return 1.0

# --------------------------
# 3. 近期推送惩罚（海量语录轮询关键）频繁推送的语录权重降低
# --------------------------
def recent_penalty(recent_push_count):
    return 1 / ((recent_push_count + 1) ** 0.7)

# --------------------------
# 4. 反馈系数：根据用户反馈调整（helpful=1.6, done=0.3, received=0.5等）
# --------------------------
def feedback_factor(fb):
    d = {"helpful":1.6, "received":0.5, "muted":0.05, "learned":0.75, "done":0.3, None:1.0}
    return d.get(fb,1.0)

# --------------------------
# 最终计算单条得分
# --------------------------
def calculate_score(saying, now, weekly_count, return_factors=False):
    it = adaptive_intensity(weekly_count)
    ff = fresh_factor(saying['create_time'], now, it)
    cf = cool_factor(saying['last_push_time'], now, it)
    rf = recent_penalty(saying['recent_push_count'])
    fb = feedback_factor(saying['last_feedback'])
    
    score = saying['base_score'] * ff * cf * rf * fb
    
    if return_factors:
        return score, {'intensity': it, 'fresh': ff, 'cool': cf, 'recent': rf, 'feedback': fb}
    return score