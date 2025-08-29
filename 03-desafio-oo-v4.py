import textwrap
from abc import ABC, abstractmethod, abstractproperty
from datetime import datetime, date


class Cliente:
    def __init__(self, endereco):
        self.endereco = endereco
        self.contas = []

    def realizar_transacao(self, conta, transacao):
        transacao.registrar(conta)

    def adicionar_conta(self, conta):
        self.contas.append(conta)


class PessoaFisica(Cliente):
    def __init__(self, nome, data_nascimento, cpf, endereco):
        super().__init__(endereco)
        self.nome = nome
        self.data_nascimento = data_nascimento
        self.cpf = cpf


class Conta:
    def __init__(self, numero, cliente):
        self._saldo = 0
        self._numero = numero
        self._agencia = "0001"
        self._cliente = cliente
        self._historico = Historico()

    @classmethod
    def nova_conta(cls, cliente, numero):
        return cls(numero, cliente)

    @property
    def saldo(self):
        return self._saldo

    @property
    def numero(self):
        return self._numero

    @property
    def agencia(self):
        return self._agencia

    @property
    def cliente(self):
        return self._cliente

    @property
    def historico(self):
        return self._historico

    def sacar(self, valor):
        if valor > self.saldo:
            print("\n@@@ Operação falhou! Saldo insuficiente. @@@")
            return False
        elif valor <= 0:
            print("\n@@@ Operação falhou! Valor inválido. @@@")
            return False
        else:
            self._saldo -= valor
            print(f"\n=== Saque de R$ {valor:.2f} realizado com sucesso! ===")
            print(f"Saldo atual: R$ {self.saldo:.2f}")
            return True

    def depositar(self, valor):
        if valor > 0:
            self._saldo += valor
            print(f"\n=== Depósito de R$ {valor:.2f} realizado com sucesso! ===")
            print(f"Saldo atual: R$ {self.saldo:.2f}")
            return True
        else:
            print("\n@@@ Operação falhou! Valor inválido. @@@")
            return False


class ContaCorrente(Conta):
    def __init__(self, numero, cliente, limite=500, limite_saques=3):
        super().__init__(numero, cliente)
        self._limite = limite
        self._limite_saques = limite_saques

    def sacar(self, valor):
        hoje = date.today()
        saques_hoje = [
            transacao for transacao in self.historico.transacoes
            if transacao["tipo"] == Saque.__name__ and
               datetime.strptime(transacao["data"], "%d-%m-%Y %H:%M:%S").date() == hoje
        ]
        numero_saques = len(saques_hoje)

        excedeu_limite = valor > self._limite
        excedeu_saques = numero_saques >= self._limite_saques

        if excedeu_limite:
            print(f"\n@@@ Operação falhou! O valor máximo por saque é R$ {self._limite:.2f}. @@@")
        elif excedeu_saques:
            print(f"\n@@@ Operação falhou! Limite diário de {self._limite_saques} saques atingido. @@@")
        else:
            return super().sacar(valor)

        return False

    def __str__(self):
        return f"""\
            Tipo:\t\tConta Corrente
            Agência:\t{self.agencia}
            C/C:\t\t{self.numero}
            Titular:\t{self.cliente.nome}
            Saldo:\t\tR$ {self.saldo:.2f}
        """


class ContaPoupanca(Conta):
    def __init__(self, numero, cliente, limite_saques=2):
        super().__init__(numero, cliente)
        self._limite_saques = limite_saques

    def sacar(self, valor):
        hoje = date.today()
        saques_hoje = [
            transacao for transacao in self.historico.transacoes
            if transacao["tipo"] == Saque.__name__ and
               datetime.strptime(transacao["data"], "%d-%m-%Y %H:%M:%S").date() == hoje
        ]
        numero_saques = len(saques_hoje)

        if valor > self.saldo:
            print("\n@@@ Operação falhou! Saldo insuficiente. @@@")
            return False
        elif valor <= 0:
            print("\n@@@ Operação falhou! Valor inválido. @@@")
            return False
        elif numero_saques >= self._limite_saques:
            print(f"\n@@@ Operação falhou! Limite diário de {self._limite_saques} saques atingido. @@@")
            return False
        else:
            self._saldo -= valor
            print(f"\n=== Saque de R$ {valor:.2f} realizado com sucesso! ===")
            print(f"Saldo atual: R$ {self.saldo:.2f}")
            return True

    def __str__(self):
        return f"""\
            Tipo:\t\tConta Poupança
            Agência:\t{self.agencia}
            C/P:\t\t{self.numero}
            Titular:\t{self.cliente.nome}
            Saldo:\t\tR$ {self.saldo:.2f}
        """


class Historico:
    def __init__(self):
        self._transacoes = []

    @property
    def transacoes(self):
        return self._transacoes

    def adicionar_transacao(self, transacao):
        self._transacoes.append(
            {
                "tipo": transacao.__class__.__name__,
                "valor": transacao.valor,
                "data": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            }
        )


class Transacao(ABC):
    @property
    @abstractmethod
    def valor(self):
        pass

    @abstractmethod
    def registrar(self, conta):
        pass


class Saque(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def registrar(self, conta):
        sucesso = conta.sacar(self.valor)
        if sucesso:
            conta.historico.adicionar_transacao(self)


class Deposito(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def registrar(self, conta):
        sucesso = conta.depositar(self.valor)
        if sucesso:
            conta.historico.adicionar_transacao(self)


def menu():
    menu = """\n
    ================ MENU ================
    [d]\tDepositar
    [s]\tSacar
    [e]\tExtrato
    [nc]\tNova conta
    [lc]\tListar contas
    [nu]\tNovo usuário
    [q]\tSair
    => """
    return input(textwrap.dedent(menu))


def exibir_saldo(conta):
    print(f"\nSaldo atual: R$ {conta.saldo:.2f}\n")


def filtrar_cliente(cpf, clientes):
    filtrados = [cliente for cliente in clientes if cliente.cpf == cpf]
    return filtrados[0] if filtrados else None


def recuperar_conta_cliente(cliente):
    if not cliente.contas:
        print("\n@@@ Cliente não possui conta! @@@")
        return None

    print("\nContas disponíveis:")
    for i, conta in enumerate(cliente.contas, 1):
        tipo = "Corrente" if isinstance(conta, ContaCorrente) else "Poupança"
        print(f"[{i}] {tipo} - Ag: {conta.agencia} C/C: {conta.numero} - Saldo: R$ {conta.saldo:.2f}")

    try:
        escolha = int(input("Selecione a conta (número): ")) - 1
        if 0 <= escolha < len(cliente.contas):
            conta = cliente.contas[escolha]
            exibir_saldo(conta)
            return conta
        else:
            print("\n@@@ Opção inválida! @@@")
            return None
    except ValueError:
        print("\n@@@ Entrada inválida! Digite um número. @@@")
        return None


def depositar(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    try:
        valor = float(input("Informe o valor do depósito: "))
        transacao = Deposito(valor)
        cliente.realizar_transacao(conta, transacao)
    except ValueError:
        print("\n@@@ Valor inválido! @@@")
        return


def sacar(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    try:
        valor = float(input("Informe o valor do saque: "))
        transacao = Saque(valor)
        cliente.realizar_transacao(conta, transacao)
    except ValueError:
        print("\n@@@ Valor inválido! @@@")
        return


def exibir_extrato(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    print("\n================ EXTRATO ================")
    transacoes = conta.historico.transacoes

    if not transacoes:
        print("Não foram realizadas movimentações.")
    else:
        for transacao in transacoes:
            data_hora = transacao["data"]
            tipo = transacao["tipo"]
            valor = transacao["valor"]
            print(f"{data_hora} - {tipo}: R$ {valor:.2f}")

    print(f"\nSaldo atual: R$ {conta.saldo:.2f}")
    print("==========================================")


def criar_cliente(clientes):
    cpf = input("Informe o CPF (somente números): ")
    if filtrar_cliente(cpf, clientes):
        print("\n@@@ Já existe cliente com esse CPF! @@@")
        return

    nome = input("Nome completo: ")
    data_nascimento = input("Data de nascimento (dd-mm-aaaa): ")
    endereco = input("Endereço (logradouro, nro - bairro - cidade/sigla estado): ")

    cliente = PessoaFisica(nome=nome, data_nascimento=data_nascimento, cpf=cpf, endereco=endereco)
    clientes.append(cliente)
    print("\n=== Cliente criado com sucesso! ===")


def criar_conta(clientes, contas):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    print("\nEscolha o tipo de conta:")
    print("[1] Conta Corrente")
    print("[2] Conta Poupança")
    try:
        opcao = int(input("Opção: "))
        numero_conta = len(contas) + 1

        if opcao == 1:
            conta = ContaCorrente.nova_conta(cliente=cliente, numero=numero_conta)
        elif opcao == 2:
            conta = ContaPoupanca.nova_conta(cliente=cliente, numero=numero_conta)
        else:
            print("\n@@@ Opção inválida! @@@")
            return

        contas.append(conta)
        cliente.contas.append(conta)
        print(f"\n=== Conta criada com sucesso! Número: {conta.numero} ===")
        print(f"Tipo: {'Corrente' if opcao == 1 else 'Poupança'}")
        exibir_saldo(conta)

    except ValueError:
        print("\n@@@ Entrada inválida! @@@")
        return


def listar_contas(contas):
    if not contas:
        print("\n@@@ Nenhuma conta cadastrada. @@@")
        return

    print("\n" + "=" * 100)
    for conta in contas:
        print(textwrap.dedent(str(conta)))
        print("=" * 100)


def main():
    clientes = []
    contas = []

    while True:
        opcao = menu()

        if opcao == "d":
            depositar(clientes)
        elif opcao == "s":
            sacar(clientes)
        elif opcao == "e":
            exibir_extrato(clientes)
        elif opcao == "nu":
            criar_cliente(clientes)
        elif opcao == "nc":
            criar_conta(clientes, contas)
        elif opcao == "lc":
            listar_contas(contas)
        elif opcao == "q":
            print("\n👋 Obrigado por usar nosso sistema bancário!")
            break
        else:
            print("\n@@@ Operação inválida! Selecione novamente. @@@")


if __name__ == "__main__":
    main()