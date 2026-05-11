-- Migration to refine tool identification
-- This allows tracking different versions and technologies of the same tool as distinct entities.

-- 1. Remove the restrictive unique constraint on 'nome'
ALTER TABLE public.ferramenta DROP CONSTRAINT IF EXISTS ferramenta_nome_key;

-- 2. Ensure identifying columns are NOT NULL for consistent unique constraint behavior
ALTER TABLE public.ferramenta ALTER COLUMN nome SET NOT NULL;
ALTER TABLE public.ferramenta ALTER COLUMN versao SET DEFAULT 'v1.0.0'; -- Default for existing data
UPDATE public.ferramenta SET versao = 'v1.0.0' WHERE versao IS NULL;
ALTER TABLE public.ferramenta ALTER COLUMN versao SET NOT NULL;

ALTER TABLE public.ferramenta ALTER COLUMN tecnologia SET DEFAULT 'Unknown';
UPDATE public.ferramenta SET tecnologia = 'Unknown' WHERE tecnologia IS NULL;
ALTER TABLE public.ferramenta ALTER COLUMN tecnologia SET NOT NULL;

-- 3. Add the composite unique constraint
ALTER TABLE public.ferramenta 
ADD CONSTRAINT ferramenta_nome_versao_tecnologia_key UNIQUE (nome, versao, tecnologia);