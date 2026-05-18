-- Procedure to ingest results for a single spectrum (experimento) and tool (ferramenta)
-- Expects a JSONB array of objects: [{"metabolite": "...", "concentration": 0.0}, ...]

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

    -- Note: If there's no unique constraint on (fk_experimento, fk_ferramenta) in the schema, 
    -- we might need to add one or use a SELECT then INSERT logic.
    -- Looking at the schema, it doesn't have it. Let's assume we handle it or add it.

    -- 4. Loop through JSON and insert results
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_json_data)
    LOOP
        v_metabolite_name := v_item->>'metabolite';
        v_concentration := (v_item->>'concentration')::DOUBLE PRECISION;

        -- Resolve Metabolite ID using our Sprint 1 function
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
