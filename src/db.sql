/*
 Navicat Premium Data Transfer

 Source Server         : localhost
 Source Server Type    : PostgreSQL
 Source Server Version : 160003 (160003)
 Source Host           : localhost:5432
 Source Catalog        : postgres
 Source Schema         : public

 Target Server Type    : PostgreSQL
 Target Server Version : 160003 (160003)
 File Encoding         : 65001

 Date: 29/06/2025 01:08:11
*/


-- ----------------------------
-- Table structure for project_tasks_amazing_prompt
-- ----------------------------
DROP TABLE IF EXISTS "public"."project_tasks_amazing_prompt";
CREATE TABLE "public"."project_tasks_amazing_prompt" (
  "id" int4 NOT NULL DEFAULT nextval('project_tasks_id_seq'::regclass),
  "key" varchar COLLATE "pg_catalog"."default",
  "project_id" varchar COLLATE "pg_catalog"."default",
  "name" varchar COLLATE "pg_catalog"."default",
  "content" varchar COLLATE "pg_catalog"."default",
  "keyword" varchar COLLATE "pg_catalog"."default",
  "business_type" varchar COLLATE "pg_catalog"."default",
  "sub_business_type" varchar COLLATE "pg_catalog"."default",
  "function_type" varchar COLLATE "pg_catalog"."default",
  "rule" varchar COLLATE "pg_catalog"."default",
  "result" varchar COLLATE "pg_catalog"."default",
  "result_gpt4" varchar COLLATE "pg_catalog"."default",
  "score" varchar(255) COLLATE "pg_catalog"."default",
  "category" varchar COLLATE "pg_catalog"."default",
  "contract_code" varchar COLLATE "pg_catalog"."default",
  "risklevel" varchar COLLATE "pg_catalog"."default",
  "similarity_with_rule" varchar(255) COLLATE "pg_catalog"."default",
  "description" varchar COLLATE "pg_catalog"."default",
  "start_line" varchar COLLATE "pg_catalog"."default",
  "end_line" varchar COLLATE "pg_catalog"."default",
  "relative_file_path" varchar COLLATE "pg_catalog"."default",
  "absolute_file_path" varchar COLLATE "pg_catalog"."default",
  "recommendation" varchar COLLATE "pg_catalog"."default",
  "title" varchar COLLATE "pg_catalog"."default",
  "business_flow_code" varchar COLLATE "pg_catalog"."default",
  "business_flow_lines" varchar COLLATE "pg_catalog"."default",
  "business_flow_context" varchar COLLATE "pg_catalog"."default",
  "if_business_flow_scan" varchar COLLATE "pg_catalog"."default"
)
;
ALTER TABLE "public"."project_tasks_amazing_prompt" OWNER TO "postgres";

-- ----------------------------
-- Indexes structure for table project_tasks_amazing_prompt
-- ----------------------------
CREATE INDEX "ix_project_tasks_key_copy1_copy1" ON "public"."project_tasks_amazing_prompt" USING btree (
  "key" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE INDEX "ix_project_tasks_project_id_copy1_copy1" ON "public"."project_tasks_amazing_prompt" USING btree (
  "project_id" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

-- ----------------------------
-- Primary Key structure for table project_tasks_amazing_prompt
-- ----------------------------
ALTER TABLE "public"."project_tasks_amazing_prompt" ADD CONSTRAINT "project_tasks_copy1_copy1_pkey" PRIMARY KEY ("id");
