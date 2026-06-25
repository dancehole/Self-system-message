-- =====================================================
-- 个人语录库 self_system_message 表
-- 兼容 Hitokoto 风格返回：id / content / type / from /
-- from_who / created_at / length
-- 字段映射：
--   content   -> plaintext
--   type      -> class
--   from      -> pin
--   from_who  -> from_who
-- =====================================================

CREATE DATABASE IF NOT EXISTS self_system
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE self_system;

CREATE TABLE IF NOT EXISTS self_system_message (
    id                  INT PRIMARY KEY AUTO_INCREMENT      COMMENT '语录主键',
    topic               VARCHAR(100)  NOT NULL              COMMENT '主题/标题',
    plaintext           TEXT          NOT NULL              COMMENT '正文（对应返回 content）',
    class               VARCHAR(50)                         COMMENT '分类（对应返回 type，可按 c 参数过滤）',
    pin                 VARCHAR(100)                        COMMENT '场景标签/出处（对应返回 from）',
    from_who            VARCHAR(100)     DEFAULT ''         COMMENT '作者/来源人物（对应返回 from_who）',
    note                TEXT                                COMMENT '备注',

    create_time         DATETIME       DEFAULT CURRENT_TIMESTAMP                                  COMMENT '创建时间',
    update_time         DATETIME       DEFAULT CURRENT_TIMESTAMP
                                      ON UPDATE CURRENT_TIMESTAMP                                 COMMENT '更新时间',

    -- 推送核心字段
    base_score          INT            DEFAULT 10          COMMENT '基础权重（人工设定的重要度）',
    last_push_time      DATETIME       NULL                COMMENT '最后推送时间',
    total_push          INT            DEFAULT 0           COMMENT '总推送次数',
    recent_push_count   INT            DEFAULT 0           COMMENT '近周期推送次数（24h 重置）',
    recent_start_time   DATETIME       NULL                COMMENT '近周期起点',

    -- 反馈
    last_feedback       VARCHAR(20)    NULL                COMMENT '最后一次反馈：helpful/received/muted/learned/done',
    last_feedback_time  DATETIME       NULL                COMMENT '最后一次反馈时间',

    -- 状态
    status              ENUM('active','muted','done')
                        DEFAULT 'active'                   COMMENT '状态：active=正常 / muted=屏蔽 / done=完成',

    INDEX idx_status        (status),
    INDEX idx_class         (class),
    INDEX idx_last_push     (last_push_time),
    INDEX idx_create_time   (create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='个人语录主表';


-- =====================================================
-- 若已存在旧表，可使用以下语句新增 from_who 字段
-- =====================================================
-- ALTER TABLE self_system_message
--   ADD COLUMN from_who VARCHAR(100) DEFAULT '' AFTER pin,
--   ADD COLUMN last_feedback_time DATETIME NULL AFTER last_feedback,
--   ADD INDEX idx_class (class);


-- =====================================================
-- 示例数据
-- =====================================================
INSERT INTO self_system_message
  (topic, plaintext, class, pin, from_who, base_score)
VALUES
  ('早睡早起', '10 点上床，6 点起床，精神一整天。', '生活', '日常', 'self', 10),
  ('阅读习惯', '每天 30 分钟，比周末突击 5 小时更有效。', '学习', '读书', 'self', 12);
