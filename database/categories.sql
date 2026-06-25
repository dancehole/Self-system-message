-- =====================================================
-- 分类管理表 categories
-- 用于存储语录分类列表，支持多选
-- =====================================================

USE self_system;

CREATE TABLE IF NOT EXISTS categories (
    id            INT PRIMARY KEY AUTO_INCREMENT      COMMENT '分类主键',
    name          VARCHAR(50)  NOT NULL UNIQUE      COMMENT '分类名称',
    sort_order    INT          DEFAULT 0             COMMENT '排序顺序',
    is_default    TINYINT(1)   DEFAULT 0            COMMENT '是否默认分类（新建时自动选中）',
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='语录分类表';

-- =====================================================
-- 默认分类数据
-- =====================================================
INSERT IGNORE INTO categories (name, sort_order, is_default) VALUES
  ('工作', 1, 0),
  ('个人提升', 2, 0),
  ('项目与产品', 3, 0),
  ('交往', 4, 0),
  ('其他', 5, 0),
  ('人生规划', 6, 0),
  ('网络', 7, 0),
  ('生活', 8, 1);
