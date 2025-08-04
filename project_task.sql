-- 创建序列
CREATE SEQUENCE IF NOT EXISTS project_task_id_seq;

-- 创建表
CREATE TABLE "public"."project_task" (
  "id" int4 NOT NULL DEFAULT nextval('project_task_id_seq'::regclass),
  "uuid" varchar(36) COLLATE "pg_catalog"."default" NOT NULL,
  "project_id" varchar(255) COLLATE "pg_catalog"."default",
  "name" varchar(500) COLLATE "pg_catalog"."default",
  "content" text COLLATE "pg_catalog"."default",
  "rule" text COLLATE "pg_catalog"."default",
  "result" text COLLATE "pg_catalog"."default",
  "contract_code" text COLLATE "pg_catalog"."default",
  "start_line" varchar(20) COLLATE "pg_catalog"."default",
  "end_line" varchar(20) COLLATE "pg_catalog"."default",
  "relative_file_path" varchar(500) COLLATE "pg_catalog"."default",
  "absolute_file_path" varchar(1000) COLLATE "pg_catalog"."default",
  "recommendation" text COLLATE "pg_catalog"."default",
  "business_flow_code" text COLLATE "pg_catalog"."default",
  "scan_record" text COLLATE "pg_catalog"."default",
  "created_at" timestamp(6) DEFAULT CURRENT_TIMESTAMP,
  "updated_at" timestamp(6) DEFAULT CURRENT_TIMESTAMP,
  "rule_key" varchar(100) COLLATE "pg_catalog"."default",
  "short_result" varchar COLLATE "pg_catalog"."default"
);

-- 设置序列的所有者（可选，但推荐）
ALTER SEQUENCE project_task_id_seq OWNED BY "public"."project_task"."id";

-- 后续的索引和约束创建保持不变
ALTER TABLE "public"."project_task" OWNER TO "postgres";

CREATE INDEX "idx_project_task_name" ON "public"."project_task" USING btree (
  "name" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE INDEX "idx_project_task_project_id" ON "public"."project_task" USING btree (
  "project_id" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE INDEX "idx_project_task_rule_key" ON "public"."project_task" USING btree (
  "rule_key" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE INDEX "idx_project_task_uuid" ON "public"."project_task" USING btree (
  "uuid" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

ALTER TABLE "public"."project_task" ADD CONSTRAINT "project_task_uuid_key" UNIQUE ("uuid");
ALTER TABLE "public"."project_task" ADD CONSTRAINT "project_task_pkey" PRIMARY KEY ("id");