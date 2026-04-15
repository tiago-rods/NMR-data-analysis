


SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE EXTENSION IF NOT EXISTS "pg_graphql" WITH SCHEMA "graphql";






CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";






CREATE OR REPLACE FUNCTION "public"."rls_auto_enable"() RETURNS "event_trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'pg_catalog'
    AS $$
DECLARE
  cmd record;
BEGIN
  FOR cmd IN
    SELECT *
    FROM pg_event_trigger_ddl_commands()
    WHERE command_tag IN ('CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO')
      AND object_type IN ('table','partitioned table')
  LOOP
     IF cmd.schema_name IS NOT NULL AND cmd.schema_name IN ('public') AND cmd.schema_name NOT IN ('pg_catalog','information_schema') AND cmd.schema_name NOT LIKE 'pg_toast%' AND cmd.schema_name NOT LIKE 'pg_temp%' THEN
      BEGIN
        EXECUTE format('alter table if exists %s enable row level security', cmd.object_identity);
        RAISE LOG 'rls_auto_enable: enabled RLS on %', cmd.object_identity;
      EXCEPTION
        WHEN OTHERS THEN
          RAISE LOG 'rls_auto_enable: failed to enable RLS on %', cmd.object_identity;
      END;
     ELSE
        RAISE LOG 'rls_auto_enable: skip % (either system schema or not in enforced list: %.)', cmd.object_identity, cmd.schema_name;
     END IF;
  END LOOP;
END;
$$;


ALTER FUNCTION "public"."rls_auto_enable"() OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."analise_comparativa" (
    "fk_experimento" integer NOT NULL,
    "fk_ferramenta_referencia" integer NOT NULL,
    "fk_ferramenta_teste" integer NOT NULL,
    "fk_metabolito" character(11) NOT NULL,
    "metodo" character varying(32)
);


ALTER TABLE "public"."analise_comparativa" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."dados_metabolitos" (
    "id_dados_metabolitos" integer NOT NULL,
    "fk_experimento" integer NOT NULL,
    "fk_ferramenta_referencia" integer NOT NULL,
    "fk_ferramenta_teste" integer NOT NULL,
    "fk_metabolito_analise" character(11) NOT NULL,
    "cobertura_percent" double precision DEFAULT 0.0 NOT NULL,
    "identificados_gs_percent" double precision DEFAULT 0.0 NOT NULL,
    CONSTRAINT "dados_metabolitos_cobertura_percent_check" CHECK ((("cobertura_percent" >= (0)::double precision) AND ("cobertura_percent" <= (100)::double precision))),
    CONSTRAINT "dados_metabolitos_identificados_gs_percent_check" CHECK ((("identificados_gs_percent" >= (0)::double precision) AND ("identificados_gs_percent" <= (100)::double precision)))
);


ALTER TABLE "public"."dados_metabolitos" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."dados_metabolitos_id_dados_metabolitos_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."dados_metabolitos_id_dados_metabolitos_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."dados_metabolitos_id_dados_metabolitos_seq" OWNED BY "public"."dados_metabolitos"."id_dados_metabolitos";



CREATE TABLE IF NOT EXISTS "public"."experimento" (
    "id_experimento" integer NOT NULL,
    "fk_instrumento" integer NOT NULL,
    "biofluido" character varying(32),
    "espectro" character varying(32)
);


ALTER TABLE "public"."experimento" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."experimento_id_experimento_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."experimento_id_experimento_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."experimento_id_experimento_seq" OWNED BY "public"."experimento"."id_experimento";



CREATE TABLE IF NOT EXISTS "public"."ferramenta" (
    "id_ferramenta" integer NOT NULL,
    "nome" character varying(50),
    "versao" character varying(10),
    "tecnologia" character varying(20),
    "tempo_medio_processamento" double precision DEFAULT 0 NOT NULL,
    CONSTRAINT "ferramenta_tempo_medio_processamento_check" CHECK (("tempo_medio_processamento" > (0)::double precision))
);


ALTER TABLE "public"."ferramenta" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."ferramenta_id_ferramenta_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."ferramenta_id_ferramenta_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."ferramenta_id_ferramenta_seq" OWNED BY "public"."ferramenta"."id_ferramenta";



CREATE TABLE IF NOT EXISTS "public"."gold_std" (
    "fk_experimento" integer NOT NULL,
    "fk_metabolito" character(11) NOT NULL,
    "concentracao_gs" double precision NOT NULL,
    CONSTRAINT "gold_std_concentracao_gs_check" CHECK (("concentracao_gs" >= (0)::double precision))
);


ALTER TABLE "public"."gold_std" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."instrumentos" (
    "id_instrumento" integer NOT NULL,
    "frequencia" double precision NOT NULL,
    "fabricante" character varying(15) NOT NULL,
    CONSTRAINT "instrumentos_frequencia_check" CHECK (("frequencia" > (0)::double precision))
);


ALTER TABLE "public"."instrumentos" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."instrumentos_id_instrumento_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."instrumentos_id_instrumento_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."instrumentos_id_instrumento_seq" OWNED BY "public"."instrumentos"."id_instrumento";



CREATE TABLE IF NOT EXISTS "public"."metabolito" (
    "id_hmdb" character(11) NOT NULL,
    "nome_padrao" character varying(100)
);


ALTER TABLE "public"."metabolito" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."metricas" (
    "id_metricas" integer NOT NULL,
    "fk_experimento" integer NOT NULL,
    "fk_ferramenta_referencia" integer NOT NULL,
    "fk_ferramenta_teste" integer NOT NULL,
    "fk_metabolito_analise" character(11) NOT NULL,
    "pearson_r" double precision DEFAULT 0.0 NOT NULL,
    "pearson_p" double precision DEFAULT 0.0 NOT NULL,
    "spearman_p" double precision DEFAULT 0.0 NOT NULL,
    "spearman_r" double precision DEFAULT 0.0 NOT NULL,
    "bias" double precision DEFAULT 0.0 NOT NULL,
    "mse" double precision DEFAULT 0.0 NOT NULL,
    "mape" double precision DEFAULT 0.0 NOT NULL,
    CONSTRAINT "metricas_mape_check" CHECK (("mape" >= (0)::double precision)),
    CONSTRAINT "metricas_mse_check" CHECK (("mse" >= (0)::double precision)),
    CONSTRAINT "metricas_pearson_p_check" CHECK (("pearson_p" >= (0)::double precision)),
    CONSTRAINT "metricas_pearson_r_check" CHECK ((("pearson_r" >= ('-1'::integer)::double precision) AND ("pearson_r" <= (1)::double precision))),
    CONSTRAINT "metricas_spearman_p_check" CHECK (("spearman_p" >= (0)::double precision)),
    CONSTRAINT "metricas_spearman_r_check" CHECK ((("spearman_r" >= ('-1'::integer)::double precision) AND ("spearman_r" <= (1)::double precision)))
);


ALTER TABLE "public"."metricas" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."metricas_id_metricas_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."metricas_id_metricas_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."metricas_id_metricas_seq" OWNED BY "public"."metricas"."id_metricas";



CREATE TABLE IF NOT EXISTS "public"."processamento" (
    "id_processamento" integer NOT NULL,
    "fk_experimento" integer NOT NULL,
    "fk_ferramenta" integer NOT NULL,
    "quantidade_metabolitos_identificados" integer DEFAULT 0 NOT NULL,
    CONSTRAINT "processamento_quantidade_metabolitos_identificados_check" CHECK (("quantidade_metabolitos_identificados" >= 0))
);


ALTER TABLE "public"."processamento" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."processamento_id_processamento_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."processamento_id_processamento_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."processamento_id_processamento_seq" OWNED BY "public"."processamento"."id_processamento";



CREATE TABLE IF NOT EXISTS "public"."resultado" (
    "fk_processamento" integer NOT NULL,
    "fk_metabolito" character(11) NOT NULL,
    "concentracao" double precision NOT NULL,
    CONSTRAINT "resultado_concentracao_check" CHECK (("concentracao" >= (0)::double precision))
);


ALTER TABLE "public"."resultado" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."schema_migrations" (
    "id" integer NOT NULL,
    "version" character varying(255) NOT NULL,
    "applied_at" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE "public"."schema_migrations" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."schema_migrations_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."schema_migrations_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."schema_migrations_id_seq" OWNED BY "public"."schema_migrations"."id";



CREATE TABLE IF NOT EXISTS "public"."sinonimo_metabolito" (
    "id_sinonimo" integer NOT NULL,
    "fk_metabolito" character(11) NOT NULL,
    "tipo_variacao" character varying(16),
    "nome_alternativo" character varying(100) NOT NULL
);


ALTER TABLE "public"."sinonimo_metabolito" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."sinonimo_metabolito_id_sinonimo_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."sinonimo_metabolito_id_sinonimo_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."sinonimo_metabolito_id_sinonimo_seq" OWNED BY "public"."sinonimo_metabolito"."id_sinonimo";



ALTER TABLE ONLY "public"."dados_metabolitos" ALTER COLUMN "id_dados_metabolitos" SET DEFAULT "nextval"('"public"."dados_metabolitos_id_dados_metabolitos_seq"'::"regclass");



ALTER TABLE ONLY "public"."experimento" ALTER COLUMN "id_experimento" SET DEFAULT "nextval"('"public"."experimento_id_experimento_seq"'::"regclass");



ALTER TABLE ONLY "public"."ferramenta" ALTER COLUMN "id_ferramenta" SET DEFAULT "nextval"('"public"."ferramenta_id_ferramenta_seq"'::"regclass");



ALTER TABLE ONLY "public"."instrumentos" ALTER COLUMN "id_instrumento" SET DEFAULT "nextval"('"public"."instrumentos_id_instrumento_seq"'::"regclass");



ALTER TABLE ONLY "public"."metricas" ALTER COLUMN "id_metricas" SET DEFAULT "nextval"('"public"."metricas_id_metricas_seq"'::"regclass");



ALTER TABLE ONLY "public"."processamento" ALTER COLUMN "id_processamento" SET DEFAULT "nextval"('"public"."processamento_id_processamento_seq"'::"regclass");



ALTER TABLE ONLY "public"."schema_migrations" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."schema_migrations_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."sinonimo_metabolito" ALTER COLUMN "id_sinonimo" SET DEFAULT "nextval"('"public"."sinonimo_metabolito_id_sinonimo_seq"'::"regclass");



ALTER TABLE ONLY "public"."analise_comparativa"
    ADD CONSTRAINT "analise_comparativa_pkey" PRIMARY KEY ("fk_experimento", "fk_ferramenta_referencia", "fk_ferramenta_teste", "fk_metabolito");



ALTER TABLE ONLY "public"."dados_metabolitos"
    ADD CONSTRAINT "dados_metabolitos_pkey" PRIMARY KEY ("id_dados_metabolitos");



ALTER TABLE ONLY "public"."experimento"
    ADD CONSTRAINT "experimento_pkey" PRIMARY KEY ("id_experimento");



ALTER TABLE ONLY "public"."ferramenta"
    ADD CONSTRAINT "ferramenta_nome_key" UNIQUE ("nome");



ALTER TABLE ONLY "public"."ferramenta"
    ADD CONSTRAINT "ferramenta_pkey" PRIMARY KEY ("id_ferramenta");



ALTER TABLE ONLY "public"."gold_std"
    ADD CONSTRAINT "gold_std_pkey" PRIMARY KEY ("fk_experimento", "fk_metabolito");



ALTER TABLE ONLY "public"."instrumentos"
    ADD CONSTRAINT "instrumentos_fabricante_key" UNIQUE ("fabricante");



ALTER TABLE ONLY "public"."instrumentos"
    ADD CONSTRAINT "instrumentos_pkey" PRIMARY KEY ("id_instrumento");



ALTER TABLE ONLY "public"."metabolito"
    ADD CONSTRAINT "metabolito_nome_padrao_key" UNIQUE ("nome_padrao");



ALTER TABLE ONLY "public"."metabolito"
    ADD CONSTRAINT "metabolito_pkey" PRIMARY KEY ("id_hmdb");



ALTER TABLE ONLY "public"."metricas"
    ADD CONSTRAINT "metricas_pkey" PRIMARY KEY ("id_metricas");



ALTER TABLE ONLY "public"."processamento"
    ADD CONSTRAINT "processamento_pkey" PRIMARY KEY ("id_processamento");



ALTER TABLE ONLY "public"."resultado"
    ADD CONSTRAINT "resultado_pkey" PRIMARY KEY ("fk_processamento", "fk_metabolito");



ALTER TABLE ONLY "public"."schema_migrations"
    ADD CONSTRAINT "schema_migrations_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."schema_migrations"
    ADD CONSTRAINT "schema_migrations_version_key" UNIQUE ("version");



ALTER TABLE ONLY "public"."sinonimo_metabolito"
    ADD CONSTRAINT "sinonimo_metabolito_pkey" PRIMARY KEY ("id_sinonimo");



ALTER TABLE ONLY "public"."analise_comparativa"
    ADD CONSTRAINT "analise_comparativa_fk_experimento_fkey" FOREIGN KEY ("fk_experimento") REFERENCES "public"."experimento"("id_experimento") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."analise_comparativa"
    ADD CONSTRAINT "analise_comparativa_fk_ferramenta_referencia_fkey" FOREIGN KEY ("fk_ferramenta_referencia") REFERENCES "public"."ferramenta"("id_ferramenta") ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."analise_comparativa"
    ADD CONSTRAINT "analise_comparativa_fk_ferramenta_teste_fkey" FOREIGN KEY ("fk_ferramenta_teste") REFERENCES "public"."ferramenta"("id_ferramenta") ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."analise_comparativa"
    ADD CONSTRAINT "analise_comparativa_fk_metabolito_fkey" FOREIGN KEY ("fk_metabolito") REFERENCES "public"."metabolito"("id_hmdb") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."experimento"
    ADD CONSTRAINT "experimento_fk_instrumento_fkey" FOREIGN KEY ("fk_instrumento") REFERENCES "public"."instrumentos"("id_instrumento") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."dados_metabolitos"
    ADD CONSTRAINT "fk_analise_comparativa" FOREIGN KEY ("fk_experimento", "fk_ferramenta_referencia", "fk_ferramenta_teste", "fk_metabolito_analise") REFERENCES "public"."analise_comparativa"("fk_experimento", "fk_ferramenta_referencia", "fk_ferramenta_teste", "fk_metabolito") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."metricas"
    ADD CONSTRAINT "fk_analise_comparativa" FOREIGN KEY ("fk_experimento", "fk_ferramenta_referencia", "fk_ferramenta_teste", "fk_metabolito_analise") REFERENCES "public"."analise_comparativa"("fk_experimento", "fk_ferramenta_referencia", "fk_ferramenta_teste", "fk_metabolito") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."gold_std"
    ADD CONSTRAINT "gold_std_fk_experimento_fkey" FOREIGN KEY ("fk_experimento") REFERENCES "public"."experimento"("id_experimento") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."gold_std"
    ADD CONSTRAINT "gold_std_fk_metabolito_fkey" FOREIGN KEY ("fk_metabolito") REFERENCES "public"."metabolito"("id_hmdb") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."processamento"
    ADD CONSTRAINT "processamento_fk_experimento_fkey" FOREIGN KEY ("fk_experimento") REFERENCES "public"."experimento"("id_experimento") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."processamento"
    ADD CONSTRAINT "processamento_fk_ferramenta_fkey" FOREIGN KEY ("fk_ferramenta") REFERENCES "public"."ferramenta"("id_ferramenta") ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."resultado"
    ADD CONSTRAINT "resultado_fk_metabolito_fkey" FOREIGN KEY ("fk_metabolito") REFERENCES "public"."metabolito"("id_hmdb") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."resultado"
    ADD CONSTRAINT "resultado_fk_processamento_fkey" FOREIGN KEY ("fk_processamento") REFERENCES "public"."processamento"("id_processamento") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."sinonimo_metabolito"
    ADD CONSTRAINT "sinonimo_metabolito_fk_metabolito_fkey" FOREIGN KEY ("fk_metabolito") REFERENCES "public"."metabolito"("id_hmdb") ON DELETE CASCADE;



ALTER TABLE "public"."analise_comparativa" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."dados_metabolitos" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."experimento" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."ferramenta" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."gold_std" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."instrumentos" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."metabolito" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."metricas" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."processamento" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."resultado" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."schema_migrations" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."sinonimo_metabolito" ENABLE ROW LEVEL SECURITY;




ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";


GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";

























































































































































GRANT ALL ON FUNCTION "public"."rls_auto_enable"() TO "anon";
GRANT ALL ON FUNCTION "public"."rls_auto_enable"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."rls_auto_enable"() TO "service_role";


















GRANT ALL ON TABLE "public"."analise_comparativa" TO "anon";
GRANT ALL ON TABLE "public"."analise_comparativa" TO "authenticated";
GRANT ALL ON TABLE "public"."analise_comparativa" TO "service_role";



GRANT ALL ON TABLE "public"."dados_metabolitos" TO "anon";
GRANT ALL ON TABLE "public"."dados_metabolitos" TO "authenticated";
GRANT ALL ON TABLE "public"."dados_metabolitos" TO "service_role";



GRANT ALL ON SEQUENCE "public"."dados_metabolitos_id_dados_metabolitos_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."dados_metabolitos_id_dados_metabolitos_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."dados_metabolitos_id_dados_metabolitos_seq" TO "service_role";



GRANT ALL ON TABLE "public"."experimento" TO "anon";
GRANT ALL ON TABLE "public"."experimento" TO "authenticated";
GRANT ALL ON TABLE "public"."experimento" TO "service_role";



GRANT ALL ON SEQUENCE "public"."experimento_id_experimento_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."experimento_id_experimento_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."experimento_id_experimento_seq" TO "service_role";



GRANT ALL ON TABLE "public"."ferramenta" TO "anon";
GRANT ALL ON TABLE "public"."ferramenta" TO "authenticated";
GRANT ALL ON TABLE "public"."ferramenta" TO "service_role";



GRANT ALL ON SEQUENCE "public"."ferramenta_id_ferramenta_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."ferramenta_id_ferramenta_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."ferramenta_id_ferramenta_seq" TO "service_role";



GRANT ALL ON TABLE "public"."gold_std" TO "anon";
GRANT ALL ON TABLE "public"."gold_std" TO "authenticated";
GRANT ALL ON TABLE "public"."gold_std" TO "service_role";



GRANT ALL ON TABLE "public"."instrumentos" TO "anon";
GRANT ALL ON TABLE "public"."instrumentos" TO "authenticated";
GRANT ALL ON TABLE "public"."instrumentos" TO "service_role";



GRANT ALL ON SEQUENCE "public"."instrumentos_id_instrumento_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."instrumentos_id_instrumento_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."instrumentos_id_instrumento_seq" TO "service_role";



GRANT ALL ON TABLE "public"."metabolito" TO "anon";
GRANT ALL ON TABLE "public"."metabolito" TO "authenticated";
GRANT ALL ON TABLE "public"."metabolito" TO "service_role";



GRANT ALL ON TABLE "public"."metricas" TO "anon";
GRANT ALL ON TABLE "public"."metricas" TO "authenticated";
GRANT ALL ON TABLE "public"."metricas" TO "service_role";



GRANT ALL ON SEQUENCE "public"."metricas_id_metricas_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."metricas_id_metricas_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."metricas_id_metricas_seq" TO "service_role";



GRANT ALL ON TABLE "public"."processamento" TO "anon";
GRANT ALL ON TABLE "public"."processamento" TO "authenticated";
GRANT ALL ON TABLE "public"."processamento" TO "service_role";



GRANT ALL ON SEQUENCE "public"."processamento_id_processamento_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."processamento_id_processamento_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."processamento_id_processamento_seq" TO "service_role";



GRANT ALL ON TABLE "public"."resultado" TO "anon";
GRANT ALL ON TABLE "public"."resultado" TO "authenticated";
GRANT ALL ON TABLE "public"."resultado" TO "service_role";



GRANT ALL ON TABLE "public"."schema_migrations" TO "anon";
GRANT ALL ON TABLE "public"."schema_migrations" TO "authenticated";
GRANT ALL ON TABLE "public"."schema_migrations" TO "service_role";



GRANT ALL ON SEQUENCE "public"."schema_migrations_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."schema_migrations_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."schema_migrations_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."sinonimo_metabolito" TO "anon";
GRANT ALL ON TABLE "public"."sinonimo_metabolito" TO "authenticated";
GRANT ALL ON TABLE "public"."sinonimo_metabolito" TO "service_role";



GRANT ALL ON SEQUENCE "public"."sinonimo_metabolito_id_sinonimo_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."sinonimo_metabolito_id_sinonimo_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."sinonimo_metabolito_id_sinonimo_seq" TO "service_role";









ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "service_role";



































drop extension if exists "pg_net";


