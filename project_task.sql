/*
 Navicat Premium Dump SQL

 Source Server         : 127.0.0.1
 Source Server Type    : PostgreSQL
 Source Server Version : 170005 (170005)
 Source Host           : localhost:5432
 Source Catalog        : postgres
 Source Schema         : public

 Target Server Type    : PostgreSQL
 Target Server Version : 170005 (170005)
 File Encoding         : 65001

 Date: 04/08/2025 16:39:50
*/


-- ----------------------------
-- Table structure for project_task
-- ----------------------------
DROP TABLE IF EXISTS "public"."project_task";
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
)
;
ALTER TABLE "public"."project_task" OWNER TO "postgres";

-- ----------------------------
-- Indexes structure for table project_task
-- ----------------------------
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

-- ----------------------------
-- Uniques structure for table project_task
-- ----------------------------
ALTER TABLE "public"."project_task" ADD CONSTRAINT "project_task_uuid_key" UNIQUE ("uuid");

-- ----------------------------
-- Primary Key structure for table project_task
-- ----------------------------
ALTER TABLE "public"."project_task" ADD CONSTRAINT "project_task_pkey" PRIMARY KEY ("id");
