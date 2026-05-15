from database.seeders.factory_seeder import FactorySeeder


class ManualSeeder(FactorySeeder):
    """
    CLI interativo para inserção manual de Ferramentas e Instrumentos.
    Herda conexão e padrão de FactorySeeder.
    """

    # ── seed() implementa o menu principal ──────────────────────────────────

    def seed(self) -> None:
        """Alias de run() para respeitar o contrato FactorySeeder."""
        self._menu_loop()

    def run(self) -> None:
        """Ponto de entrada — sobrescreve run() para exibir o menu CLI."""
        self._menu_loop()

    # ── Helpers internos ─────────────────────────────────────────────────────

    def _obter_tempo_input(self) -> float | None:
        print("\nEscolha como deseja inserir o tempo:")
        print("1. Tempo médio por espectro diretamente (segundos)")
        print("2. Tempo total do perfilamento (será dividido pelo nº de espectros)")

        escolha = input("Escolha (1-2): ").strip()

        try:
            if escolha == "1":
                return float(input("Tempo médio por espectro (s): ").strip())
            elif escolha == "2":
                tempo_total = float(input("Tempo total do perfilamento (s): ").strip())
                num_espectros = int(
                    input("Quantidade de espectros na amostra: ").strip()
                )
                if num_espectros <= 0:
                    print("Erro: A quantidade de espectros deve ser maior que zero.")
                    return None
                tempo_calc = tempo_total / num_espectros
                print(f"Tempo médio calculado: {tempo_calc:.4f} s/espectro")
                return tempo_calc
            else:
                print("Escolha inválida.")
                return None
        except ValueError:
            print("Valor numérico inválido.")
            return None

    def upsert_ferramenta(self) -> None:
        print("\n--- Cadastro/Atualização de Ferramenta ---")
        print(
            "Lembre-se: Cada combinação de Nome, Versão e Tecnologia é tratada"
            " como uma entrada única."
        )

        nome = input("Nome da Ferramenta (ex: nmRanalysis, ASICS): ").strip()
        if not nome:
            return

        versao = input("Versão (padrão 'v1.0.0'): ").strip() or "v1.0.0"
        tecnologia = (
            input("Tecnologia (ex: R, Python - padrão 'Unknown'): ").strip()
            or "Unknown"
        )

        print("\nDeseja definir/atualizar o tempo de processamento?")
        print("1. Sim")
        print("2. Não (manter atual ou padrão)")
        op_tempo = input("Escolha: ").strip()

        tempo_medio = None
        if op_tempo == "1":
            tempo_medio = self._obter_tempo_input()

        data = {"nome": nome, "versao": versao, "tecnologia": tecnologia}
        if tempo_medio is not None:
            data["tempo_medio_processamento"] = tempo_medio

        try:
            self.supabase.table("ferramenta").upsert(
                data, on_conflict="nome,versao,tecnologia"
            ).execute()
            print(
                f"\nSucesso! Ferramenta '{nome}' versão '{versao}' ({tecnologia})"
                " salva no banco."
            )
        except Exception as e:
            print(f"Erro ao salvar ferramenta: {e}")

    def seed_instrumento(self) -> None:
        print("\n--- Cadastro de Instrumento ---")
        fabricante = input("Fabricante (ex: Agilent, Bruker): ").strip()
        if not fabricante:
            return

        try:
            freq = float(
                input("Frequência (MHz) (ex: 500.0, 600.0): ").strip()
            )
        except ValueError:
            print("Frequência inválida. Cancelando inserção.")
            return

        data = {"fabricante": fabricante, "frequencia": freq}

        try:
            self.supabase.table("instrumentos").upsert(
                data, on_conflict="fabricante"
            ).execute()
            print(f"Instrumento '{fabricante} ({freq}MHz)' inserido com sucesso!")
        except Exception as e:
            print(f"Erro ao inserir instrumento: {e}")

    def _menu_loop(self) -> None:
        while True:
            print("\nO que você deseja fazer?")
            print("1. Cadastrar/Atualizar Ferramenta (Nome + Versão + Tecnologia)")
            print("2. Cadastrar/Atualizar Instrumento")
            print("0. Sair")

            choice = input("Escolha (0-2): ").strip()

            if choice == "1":
                self.upsert_ferramenta()
            elif choice == "2":
                self.seed_instrumento()
            elif choice == "0":
                print("Saindo do Manual Seeder.")
                break
            else:
                print("Escolha inválida.")


if __name__ == "__main__":
    seeder = ManualSeeder()
    seeder.run()
