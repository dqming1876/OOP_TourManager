-- Preserve original JSON for rollback/manual comparison; runtime uses scalar columns.
CREATE TABLE legacy_tour_content AS SELECT id, content FROM tours;
ALTER TABLE tours ADD COLUMN "title" TEXT NOT NULL DEFAULT '';
ALTER TABLE tours ADD COLUMN "province" TEXT NOT NULL DEFAULT '';
ALTER TABLE tours ADD COLUMN "place" TEXT NOT NULL DEFAULT '';
ALTER TABLE tours ADD COLUMN "days" INTEGER NOT NULL DEFAULT 1 CHECK(days BETWEEN 1 AND 30);
ALTER TABLE tours ADD COLUMN "desc" TEXT NOT NULL DEFAULT '';
ALTER TABLE tours ADD COLUMN "category" TEXT NOT NULL DEFAULT '';
ALTER TABLE tours ADD COLUMN "pickup" TEXT NOT NULL DEFAULT '';
ALTER TABLE tours ADD COLUMN "includes" TEXT NOT NULL DEFAULT '';
ALTER TABLE tours ADD COLUMN "excludes" TEXT NOT NULL DEFAULT '';
ALTER TABLE tours ADD COLUMN "coverSource" TEXT NOT NULL DEFAULT '';
ALTER TABLE tours ADD COLUMN "cover" TEXT NOT NULL DEFAULT '';
UPDATE tours SET "title" = COALESCE(json_extract(content,'$.title'), ''), "province" = COALESCE(json_extract(content,'$.province'), ''), "place" = COALESCE(json_extract(content,'$.place'), ''), "days" = COALESCE(json_extract(content,'$.days'), 1), "desc" = COALESCE(json_extract(content,'$.desc'), ''), "category" = COALESCE(json_extract(content,'$.category'), ''), "pickup" = COALESCE(json_extract(content,'$.pickup'), ''), "includes" = COALESCE(json_extract(content,'$.includes'), ''), "excludes" = COALESCE(json_extract(content,'$.excludes'), ''), "coverSource" = COALESCE(json_extract(content,'$.coverSource'), ''), "cover" = COALESCE(json_extract(content,'$.cover'), '');
ALTER TABLE tours DROP COLUMN content;
