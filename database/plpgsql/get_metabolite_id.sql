-- Function to resolve a metabolite ID from a given name (standard name or synonym)
CREATE OR REPLACE FUNCTION get_metabolite_id(p_name TEXT) 
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
