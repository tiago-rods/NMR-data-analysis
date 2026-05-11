-- Procedure to ingest Gold Standard results for a single spectrum
-- Expects a JSONB array of objects: [{"metabolite": "...", "concentration": 0.0}, ...]

CREATE OR REPLACE PROCEDURE public.ingest_gold_standard(
    p_espectro_name VARCHAR,
    p_json_data JSONB
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_fk_experimento INTEGER;
    v_item JSONB;
    v_fk_metabolito CHAR(11);
    v_metabolite_name VARCHAR;
    v_concentration DOUBLE PRECISION;
BEGIN
    -- 1. Resolve Experiment ID
    SELECT id_experimento INTO v_fk_experimento 
    FROM public.experimento 
    WHERE espectro = p_espectro_name
    LIMIT 1;

    IF v_fk_experimento IS NULL THEN
        -- Optionally, we could create the experiment here if it doesn't exist
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
