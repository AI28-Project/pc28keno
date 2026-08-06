-- pc28keno 基础表结构 + 种子数据
-- 用法: psql -d api -f sql/schema.sql

BEGIN;

CREATE TABLE IF NOT EXISTS keno (
    draw_nbr    BIGINT PRIMARY KEY,
    draw_date   VARCHAR(32),
    draw_time   VARCHAR(32),
    draw_nbrs   INTEGER[],
    draw_bonus  INTEGER,
    countdown   VARCHAR(32),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS number (
    draw_nbr          BIGINT PRIMARY KEY,
    draw_date         VARCHAR(32),
    draw_time         VARCHAR(32),
    draw_number       VARCHAR(32),
    draw_num          INTEGER,
    source            VARCHAR(32),
    size_type         VARCHAR(16),
    parity_type       VARCHAR(16),
    extreme_type      VARCHAR(16),
    combination_type  VARCHAR(16),
    pattern_type      VARCHAR(16),
    location_type     VARCHAR(16),
    dragon_tiger      VARCHAR(16),
    omission_done     BOOLEAN,
    statistics_done   BOOLEAN,
    dragon_done       BOOLEAN,
    abc_omission_done BOOLEAN,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS omission (
    missing_content VARCHAR(32) PRIMARY KEY,
    missing_data    INTEGER NOT NULL DEFAULT 0,
    missed_time     TIMESTAMPTZ DEFAULT NOW(),
    sort_order      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS abc_omission (
    missing_content VARCHAR(32) PRIMARY KEY,
    missing_data    INTEGER NOT NULL DEFAULT 0,
    missed_time     TIMESTAMPTZ DEFAULT NOW(),
    sort_order      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS statistics (
    statistics_content VARCHAR(32) PRIMARY KEY,
    statistics_data    INTEGER NOT NULL DEFAULT 0,
    statistics_time    TIMESTAMPTZ DEFAULT NOW(),
    sort_order         INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS dragon (
    dragon_type     VARCHAR(32) NOT NULL,
    dragon_content  VARCHAR(32) NOT NULL,
    dragon_count    INTEGER DEFAULT 0,
    dragon_start    VARCHAR(64),
    dragon_current  VARCHAR(64),
    dragon_sequence TEXT,
    dragon_expected VARCHAR(64),
    dragon_status   VARCHAR(16) DEFAULT '已断开',
    status_order    INTEGER DEFAULT 1,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    dragon_time     TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (dragon_type, dragon_content)
);

CREATE INDEX IF NOT EXISTS idx_number_omission_pending
    ON number (draw_nbr) WHERE (omission_done IS NULL OR omission_done = false);
CREATE INDEX IF NOT EXISTS idx_number_abc_omission_pending
    ON number (draw_nbr) WHERE (abc_omission_done IS NULL OR abc_omission_done = false);
CREATE INDEX IF NOT EXISTS idx_number_statistics_pending
    ON number (draw_nbr) WHERE (statistics_done IS NULL OR statistics_done = false);
CREATE INDEX IF NOT EXISTS idx_number_dragon_pending
    ON number (draw_nbr) WHERE (dragon_done IS NULL OR dragon_done = false);


-- 遗漏 / 统计种子（60 项）
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('00', 0, 0) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('00', 0, 0) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('01', 0, 1) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('01', 0, 1) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('02', 0, 2) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('02', 0, 2) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('03', 0, 3) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('03', 0, 3) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('04', 0, 4) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('04', 0, 4) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('05', 0, 5) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('05', 0, 5) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('06', 0, 6) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('06', 0, 6) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('07', 0, 7) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('07', 0, 7) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('08', 0, 8) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('08', 0, 8) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('09', 0, 9) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('09', 0, 9) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('10', 0, 10) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('10', 0, 10) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('11', 0, 11) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('11', 0, 11) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('12', 0, 12) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('12', 0, 12) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('13', 0, 13) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('13', 0, 13) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('14', 0, 14) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('14', 0, 14) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('15', 0, 15) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('15', 0, 15) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('16', 0, 16) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('16', 0, 16) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('17', 0, 17) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('17', 0, 17) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('18', 0, 18) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('18', 0, 18) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('19', 0, 19) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('19', 0, 19) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('20', 0, 20) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('20', 0, 20) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('21', 0, 21) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('21', 0, 21) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('22', 0, 22) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('22', 0, 22) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('23', 0, 23) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('23', 0, 23) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('24', 0, 24) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('24', 0, 24) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('25', 0, 25) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('25', 0, 25) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('26', 0, 26) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('26', 0, 26) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('27', 0, 27) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('27', 0, 27) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('大', 0, 28) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('大', 0, 28) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('小', 0, 29) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('小', 0, 29) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('单', 0, 30) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('单', 0, 30) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('双', 0, 31) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('双', 0, 31) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('龙', 0, 32) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('龙', 0, 32) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('虎', 0, 33) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('虎', 0, 33) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('合', 0, 34) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('合', 0, 34) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('小单', 0, 35) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('小单', 0, 35) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('小双', 0, 36) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('小双', 0, 36) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('大单', 0, 37) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('大单', 0, 37) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('大双', 0, 38) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('大双', 0, 38) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('小边', 0, 39) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('小边', 0, 39) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('中', 0, 40) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('中', 0, 40) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('大边', 0, 41) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('大边', 0, 41) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('极大', 0, 42) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('极大', 0, 42) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('极小', 0, 43) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('极小', 0, 43) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('对子', 0, 44) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('对子', 0, 44) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('顺子', 0, 45) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('顺子', 0, 45) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('豹子', 0, 46) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('豹子', 0, 46) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('杂六', 0, 47) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('杂六', 0, 47) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('3N余0', 0, 48) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('3N余0', 0, 48) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('3N余1', 0, 49) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('3N余1', 0, 49) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('3N余2', 0, 50) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('3N余2', 0, 50) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('4N余0', 0, 51) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('4N余0', 0, 51) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('4N余1', 0, 52) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('4N余1', 0, 52) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('4N余2', 0, 53) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('4N余2', 0, 53) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('4N余3', 0, 54) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('4N余3', 0, 54) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('5N余0', 0, 55) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('5N余0', 0, 55) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('5N余1', 0, 56) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('5N余1', 0, 56) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('5N余2', 0, 57) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('5N余2', 0, 57) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('5N余3', 0, 58) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('5N余3', 0, 58) ON CONFLICT (statistics_content) DO NOTHING;
INSERT INTO omission (missing_content, missing_data, sort_order) VALUES ('5N余4', 0, 59) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO statistics (statistics_content, statistics_data, sort_order) VALUES ('5N余4', 0, 59) ON CONFLICT (statistics_content) DO NOTHING;

-- ABC 球遗漏种子（54 项）
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('a0', 0, 0) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('a1', 0, 1) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('a2', 0, 2) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('a3', 0, 3) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('a4', 0, 4) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('a5', 0, 5) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('a6', 0, 6) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('a7', 0, 7) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('a8', 0, 8) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('a9', 0, 9) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('a大', 0, 10) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('a小', 0, 11) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('a单', 0, 12) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('a双', 0, 13) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('a小单', 0, 14) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('a小双', 0, 15) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('a大单', 0, 16) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('a大双', 0, 17) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('b0', 0, 18) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('b1', 0, 19) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('b2', 0, 20) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('b3', 0, 21) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('b4', 0, 22) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('b5', 0, 23) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('b6', 0, 24) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('b7', 0, 25) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('b8', 0, 26) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('b9', 0, 27) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('b大', 0, 28) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('b小', 0, 29) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('b单', 0, 30) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('b双', 0, 31) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('b小单', 0, 32) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('b小双', 0, 33) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('b大单', 0, 34) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('b大双', 0, 35) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('c0', 0, 36) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('c1', 0, 37) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('c2', 0, 38) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('c3', 0, 39) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('c4', 0, 40) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('c5', 0, 41) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('c6', 0, 42) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('c7', 0, 43) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('c8', 0, 44) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('c9', 0, 45) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('c大', 0, 46) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('c小', 0, 47) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('c单', 0, 48) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('c双', 0, 49) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('c小单', 0, 50) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('c小双', 0, 51) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('c大单', 0, 52) ON CONFLICT (missing_content) DO NOTHING;
INSERT INTO abc_omission (missing_content, missing_data, sort_order) VALUES ('c大双', 0, 53) ON CONFLICT (missing_content) DO NOTHING;

-- 长龙种子行
INSERT INTO dragon (dragon_type, dragon_content, dragon_status, status_order, sort_order) VALUES ('循环', '大小', '已断开', 1, 0) ON CONFLICT (dragon_type, dragon_content) DO NOTHING;
INSERT INTO dragon (dragon_type, dragon_content, dragon_status, status_order, sort_order) VALUES ('循环', '单双', '已断开', 1, 1) ON CONFLICT (dragon_type, dragon_content) DO NOTHING;
INSERT INTO dragon (dragon_type, dragon_content, dragon_status, status_order, sort_order) VALUES ('循环', '组合', '已断开', 1, 2) ON CONFLICT (dragon_type, dragon_content) DO NOTHING;
INSERT INTO dragon (dragon_type, dragon_content, dragon_status, status_order, sort_order) VALUES ('循环', '龙虎', '已断开', 1, 3) ON CONFLICT (dragon_type, dragon_content) DO NOTHING;
INSERT INTO dragon (dragon_type, dragon_content, dragon_status, status_order, sort_order) VALUES ('循环', '边中', '已断开', 1, 4) ON CONFLICT (dragon_type, dragon_content) DO NOTHING;
INSERT INTO dragon (dragon_type, dragon_content, dragon_status, status_order, sort_order) VALUES ('交替', '大小', '已断开', 1, 5) ON CONFLICT (dragon_type, dragon_content) DO NOTHING;
INSERT INTO dragon (dragon_type, dragon_content, dragon_status, status_order, sort_order) VALUES ('交替', '单双', '已断开', 1, 6) ON CONFLICT (dragon_type, dragon_content) DO NOTHING;
INSERT INTO dragon (dragon_type, dragon_content, dragon_status, status_order, sort_order) VALUES ('交替', '组合', '已断开', 1, 7) ON CONFLICT (dragon_type, dragon_content) DO NOTHING;
INSERT INTO dragon (dragon_type, dragon_content, dragon_status, status_order, sort_order) VALUES ('交替', '龙虎', '已断开', 1, 8) ON CONFLICT (dragon_type, dragon_content) DO NOTHING;
INSERT INTO dragon (dragon_type, dragon_content, dragon_status, status_order, sort_order) VALUES ('交替', '边中', '已断开', 1, 9) ON CONFLICT (dragon_type, dragon_content) DO NOTHING;
INSERT INTO dragon (dragon_type, dragon_content, dragon_status, status_order, sort_order) VALUES ('abb循环', '大小', '已断开', 1, 10) ON CONFLICT (dragon_type, dragon_content) DO NOTHING;
INSERT INTO dragon (dragon_type, dragon_content, dragon_status, status_order, sort_order) VALUES ('abb循环', '单双', '已断开', 1, 11) ON CONFLICT (dragon_type, dragon_content) DO NOTHING;
INSERT INTO dragon (dragon_type, dragon_content, dragon_status, status_order, sort_order) VALUES ('abb循环', '组合', '已断开', 1, 12) ON CONFLICT (dragon_type, dragon_content) DO NOTHING;
INSERT INTO dragon (dragon_type, dragon_content, dragon_status, status_order, sort_order) VALUES ('abb循环', '龙虎', '已断开', 1, 13) ON CONFLICT (dragon_type, dragon_content) DO NOTHING;
INSERT INTO dragon (dragon_type, dragon_content, dragon_status, status_order, sort_order) VALUES ('abb循环', '边中', '已断开', 1, 14) ON CONFLICT (dragon_type, dragon_content) DO NOTHING;
INSERT INTO dragon (dragon_type, dragon_content, dragon_status, status_order, sort_order) VALUES ('赔率循环', '赔率', '已断开', 1, 15) ON CONFLICT (dragon_type, dragon_content) DO NOTHING;

COMMIT;
