-- Migration to support atomic ingestion and prevent duplicates

-- 1. Processamento: Each experiment should have only one processing entry per tool version
ALTER TABLE public.processamento 
ADD CONSTRAINT processamento_fk_experimento_fk_ferramenta_key UNIQUE (fk_experimento, fk_ferramenta);

-- 2. Resultado: Each processing should have only one concentration per metabolite
ALTER TABLE public.resultado 
ADD CONSTRAINT resultado_fk_processamento_fk_metabolito_key UNIQUE (fk_processamento, fk_metabolito);

-- 3. Gold Standard: Each experiment (spectrum) has one reference concentration per metabolite
ALTER TABLE public.gold_std 
ADD CONSTRAINT gold_std_fk_experimento_fk_metabolito_key UNIQUE (fk_experimento, fk_metabolito);

-- 4. Experimento: Spectrum names should be unique
ALTER TABLE public.experimento 
ADD CONSTRAINT experimento_espectro_key UNIQUE (espectro);

-- 5. Instrumentos: Frequency and Fabricant combination should be unique
ALTER TABLE public.instrumentos 
ADD CONSTRAINT instrumentos_frequencia_fabricante_key UNIQUE (frequencia, fabricante);

-- 6. Ferramenta: Name, Version and Technology combination should be unique
ALTER TABLE public.ferramenta 
ADD CONSTRAINT ferramenta_nome_versao_tecnologia_key UNIQUE (nome, versao, tecnologia);
