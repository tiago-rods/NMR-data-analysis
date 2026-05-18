-- Migration to deploy custom PL/pgSQL functions, procedures, and triggers

-- 1. Helper function to clean spectrum names (removing suffixes like _ex1_p1)
CREATE OR REPLACE FUNCTION public.clean_espectro_name_func(raw_name VARCHAR)
RETURNS VARCHAR
LANGUAGE plpgsql
AS $$
DECLARE
    cleaned VARCHAR;
BEGIN
    -- Remove apenas o sufixo _ex1_p1 e _ex_p1
    cleaned := replace(raw_name, '_ex1_p1', '');
    cleaned := replace(cleaned, '_ex_p1', '');
    
    -- Se a remoção deixar dois underscores seguidos (ex: algo__LNBio), transforma em um só
    cleaned := replace(cleaned, '__', '_');
    
    RETURN cleaned;
END;
$$;

-- 2. Trigger function to clean spectrum names before insert or update on public.experimento
CREATE OR REPLACE FUNCTION public.trg_clean_espectro_name()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.espectro := public.clean_espectro_name_func(NEW.espectro);
    RETURN NEW;
END;
$$;

-- 3. Create the clean_espectro_before_insert trigger
DROP TRIGGER IF EXISTS clean_espectro_before_insert ON public.experimento;
CREATE TRIGGER clean_espectro_before_insert
BEFORE INSERT OR UPDATE ON public.experimento
FOR EACH ROW EXECUTE FUNCTION public.trg_clean_espectro_name();

-- 4. Function to resolve metabolite ID from HMDB standard name or synonym
CREATE OR REPLACE FUNCTION public.get_metabolite_id(p_name TEXT) 
RETURNS CHAR(11) AS $$
DECLARE
    v_id CHAR(11);
BEGIN
    -- 1. Try to find by standard name first (exact match, case insensitive)
    SELECT id_hmdb INTO v_id 
    FROM public.metabolito 
    WHERE LOWER(nome_padrao) = LOWER(p_name);
    
    IF FOUND THEN 
        RETURN v_id; 
    END IF;

    -- 2. If not found, try to find in the synonyms table
    SELECT fk_metabolito INTO v_id 
    FROM public.sinonimo_metabolito 
    WHERE LOWER(nome_alternativo) = LOWER(p_name) 
    LIMIT 1;
    
    -- 3. Return the ID or NULL if it wasn't found anywhere
    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

-- 5. Procedure to ingest experiment results (FUNCTION returning void for PostgREST compatibility)
CREATE OR REPLACE FUNCTION public.ingest_experiment_results(
    p_espectro_name VARCHAR,
    p_tool_name VARCHAR,
    p_tool_version VARCHAR,
    p_tool_tech VARCHAR,
    p_json_data JSONB
)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    v_fk_experimento INTEGER;
    v_fk_ferramenta INTEGER;
    v_fk_processamento INTEGER;
    v_item JSONB;
    v_fk_metabolito CHAR(11);
    v_metabolite_name VARCHAR;
    v_concentration DOUBLE PRECISION;
    v_count INTEGER := 0;
BEGIN
    -- 0. Limpar o nome do espectro (removendo _ex1_p1 e afins)
    p_espectro_name := public.clean_espectro_name_func(p_espectro_name);

    -- 1. Resolve Experiment ID from spectrum name
    SELECT id_experimento INTO v_fk_experimento 
    FROM public.experimento 
    WHERE espectro = p_espectro_name
    LIMIT 1;

    IF v_fk_experimento IS NULL THEN
        RAISE EXCEPTION 'Experiment with spectrum name % not found.', p_espectro_name;
    END IF;

    -- 2. Resolve Tool ID
    SELECT id_ferramenta INTO v_fk_ferramenta 
    FROM public.ferramenta 
    WHERE nome = p_tool_name 
      AND versao = p_tool_version 
      AND tecnologia = p_tool_tech
    LIMIT 1;

    IF v_fk_ferramenta IS NULL THEN
        RAISE EXCEPTION 'Tool % (%) % not found.', p_tool_name, p_tool_version, p_tool_tech;
    END IF;

    -- 3. Create Processing entry (upsert)
    INSERT INTO public.processamento (fk_experimento, fk_ferramenta)
    VALUES (v_fk_experimento, v_fk_ferramenta)
    ON CONFLICT (fk_experimento, fk_ferramenta) DO UPDATE 
    SET fk_experimento = EXCLUDED.fk_experimento -- effectively a no-op to get the ID
    RETURNING id_processamento INTO v_fk_processamento;

    -- 4. Loop through JSON and insert results
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_json_data)
    LOOP
        v_metabolite_name := v_item->>'metabolite';
        v_concentration := (v_item->>'concentration')::DOUBLE PRECISION;

        -- Resolve Metabolite ID using our function
        v_fk_metabolito := public.get_metabolite_id(v_metabolite_name);

        IF v_fk_metabolito IS NOT NULL THEN
            INSERT INTO public.resultado (fk_processamento, fk_metabolito, concentracao)
            VALUES (v_fk_processamento, v_fk_metabolito, v_concentration)
            ON CONFLICT (fk_processamento, fk_metabolito) DO UPDATE 
            SET concentracao = EXCLUDED.concentracao;
            
            v_count := v_count + 1;
        END IF;
    END LOOP;

    -- 5. Update identified count
    UPDATE public.processamento 
    SET quantidade_metabolitos_identificados = v_count 
    WHERE id_processamento = v_fk_processamento;

END;
$$;

-- 6. Procedure to ingest Gold Standard results (FUNCTION returning void for PostgREST compatibility)
CREATE OR REPLACE FUNCTION public.ingest_gold_standard(
    p_espectro_name VARCHAR,
    p_json_data JSONB
)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    v_fk_experimento INTEGER;
    v_item JSONB;
    v_fk_metabolito CHAR(11);
    v_metabolite_name VARCHAR;
    v_concentration DOUBLE PRECISION;
BEGIN
    -- 0. Limpar o nome do espectro
    p_espectro_name := public.clean_espectro_name_func(p_espectro_name);

    -- 1. Resolve Experiment ID
    SELECT id_experimento INTO v_fk_experimento 
    FROM public.experimento 
    WHERE espectro = p_espectro_name
    LIMIT 1;

    IF v_fk_experimento IS NULL THEN
        RAISE EXCEPTION 'Experiment with spectrum name % not found. Reference data requires a pre-existing experiment.', p_espectro_name;
    END IF;

    -- 2. Loop through JSON and insert into gold_std
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_json_data)
    LOOP
        v_metabolite_name := v_item->>'metabolite';
        v_concentration := (v_item->>'concentration')::DOUBLE PRECISION;

        -- Resolve Metabolite ID
        v_fk_metabolito := public.get_metabolite_id(v_metabolite_name);

        IF v_fk_metabolito IS NOT NULL THEN
            INSERT INTO public.gold_std (fk_experimento, fk_metabolito, concentracao_gs)
            VALUES (v_fk_experimento, v_fk_metabolito, v_concentration)
            ON CONFLICT (fk_experimento, fk_metabolito) DO UPDATE 
            SET concentracao_gs = EXCLUDED.concentracao_gs;
        END IF;
    END LOOP;

END;
$$;
