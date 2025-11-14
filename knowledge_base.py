from sympy import symbols, Not, And, Or, to_cnf, Equivalent, Implies


def pl_resolve(clause1, clause2):
    """
    Resolve two clauses
    Args:
        clause1 (str): Clause 1
        clause2 (str): Clause 2
    Returns:
        list: Resolvents
    """
    resolvents = []
    for literal1 in clause1:
        for literal2 in clause2:
            if literal1 == Not(literal2) or literal2 == Not(literal1):
                # remove the literals from the clauses
                clause1_copy = set(clause1)
                clause2_copy = set(clause2)
                clause1_copy.remove(literal1)
                clause2_copy.remove(literal2)
                resolvents.append(frozenset(clause1_copy.union(clause2_copy)))
    return resolvents


def get_clauses(cnf):
    if isinstance(cnf, And):
        return list(cnf.args)
    else:
        return [cnf]


def get_literals(clause):
    if isinstance(clause, Or):
        return clause.args
    else:
        return [clause]


class KnowledgeBase:
    hasArrow = True
    hasGold = False

    def __init__(self):
        self.clauses = set()  # Knowledge base
        self.reward = 0
        # Add initial knowledge to knowledge base
        self.clauses.update([Not(symbols("P00"))])
        self.clauses.update([Not(symbols("W00"))])
        self.clauses.update([Not(symbols("G00"))])

    def tell_test(self):
        expression = Equivalent(Not(symbols("S00")), And(Not(symbols("W01")), Not(symbols("W10"))))
        expression_cnf = to_cnf(expression)
        self.clauses.update(get_clauses(expression_cnf))
        # expression = Equivalent(Not(symbols("B00")), Or(Not(symbols("P01")), Not(symbols("P10"))))

    def tell(self, observation, reward: float):
        x = observation['x']
        y = observation['y']

        # Add visited field to knowledge base
        V = symbols(f"V{x}{y}")
        self.clauses.update([V])
        # On a visited field there is no pit nor wumpus
        expression = Implies(V, And(Not(symbols(f"P{x}{y}")), Not(symbols(f"W{x}{y}"))))
        expression_cnf = to_cnf(expression)
        self.clauses.update(get_clauses(expression_cnf))

        # Add Scream if wumpus is dead
        if observation['scream']:
            for i in range(4):
                for j in range(4):
                    self.clauses.update([Not(symbols(f"W{i}{j}"))])

        # Add if glitter is present
        if observation['glitter']:
            self.clauses.update([symbols(f"G{x}{y}")])

        evaluate = []
        if observation['breeze']:
            evaluate.append(('B', 'P', True))
        else:
            evaluate.append(('B', 'P', False))
        if observation['stench']:
            evaluate.append(('S', 'W', True))
        else:
            evaluate.append(('S', 'W', False))

        for e, f, true in evaluate:
            beta = []
            if true:
                self.clauses.update([symbols(f"{e}{x}{y}")])
                alpha = symbols(f"{e}{x}{y}")
                if x - 1 >= 0:
                    beta.append(symbols(f"{f}{x - 1}{y}"))
                if x + 1 < 4:
                    beta.append(symbols(f"{f}{x + 1}{y}"))
                if y - 1 >= 0:
                    beta.append(symbols(f"{f}{x}{y - 1}"))
                if y + 1 < 4:
                    beta.append(symbols(f"{f}{x}{y + 1}"))
                if f == 'W':
                    beta.append(symbols(f"{f}{x}{y}"))
            else:
                self.clauses.update([Not(symbols(f"{e}{x}{y}"))])
                alpha = Not(symbols(f"{e}{x}{y}"))
                if x - 1 >= 0:
                    beta.append(Not(symbols(f"{f}{x - 1}{y}")))
                if x + 1 < 4:
                    beta.append(Not(symbols(f"{f}{x + 1}{y}")))
                if y - 1 >= 0:
                    beta.append(Not(symbols(f"{f}{x}{y - 1}")))
                if y + 1 < 4:
                    beta.append(Not(symbols(f"{f}{x}{y + 1}")))
                if f == 'W':
                    beta.append(Not(symbols(f"{f}{x}{y}")))

            beta = Or(*beta)
            expression = Equivalent(alpha, beta)
            # print("Expression:", expression)
            expression_cnf = to_cnf(expression)
            self.clauses.update(get_clauses(expression_cnf))

    def ask(self, proposition):
        """
        Ask the knowledge base about a proposition
        Args:
            proposition (str): Proposition
        Returns:
            bool: True if the proposition is true, False otherwise
        """
        return self.pl_resolution(proposition)

    def pl_resolution(self, alpha):
        """
        PL-Resolution algorithm
        Args:
            alpha (str): Proposition
        Returns:
            bool: True if the proposition is true, False otherwise
        """
        clauses = self.clauses.union([Not(alpha)])
        clauses = [frozenset(get_literals(c)) for c in clauses]
        print("Clauses:", clauses)
        new = set()
        while True:
            for i in range(len(clauses)):
                for j in range(i + 1, len(clauses)):
                    resolvents = pl_resolve(clauses[i], clauses[j])
                    if frozenset() in resolvents:
                        return True
                    new.update(resolvents)
                    #print("New:", new)
            # convert clauses to list of frozensets to be able to compare them
            clauses = [frozenset(c) for c in clauses]
            if new.issubset(set(clauses)):
                return False
            clauses += list(new)
            # convert to list of sets, to be able to resolve them again
            clauses = [set(c) for c in clauses]
            # print("Clauses:", clauses)
