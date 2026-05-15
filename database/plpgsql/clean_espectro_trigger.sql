-- Função utilitária para limpar sufixos e prefixos dos nomes de espectros
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

-- Função do Trigger
CREATE OR REPLACE FUNCTION public.trg_clean_espectro_name()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.espectro := public.clean_espectro_name_func(NEW.espectro);
    RETURN NEW;
END;
$$;

-- Associar o Trigger à tabela experimento
DROP TRIGGER IF EXISTS clean_espectro_before_insert ON public.experimento;
CREATE TRIGGER clean_espectro_before_insert
BEFORE INSERT OR UPDATE ON public.experimento
FOR EACH ROW EXECUTE FUNCTION public.trg_clean_espectro_name();
