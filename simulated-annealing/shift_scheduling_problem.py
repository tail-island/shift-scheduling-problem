from deap      import algorithms, base, creator, tools
from functools import reduce
from funcy     import *
from random    import randint, random, seed

M = 5   # 社員の数
D = 10  # 日数

# 評価関数
def evaluate(individual):
    # 1日に2名以上、かつ、できるだけ少なくという制約を追加します。2名より多くても少なくてもペナルティが発生するようになっています
    def member_size():
        result = 0

        for d in range(D):
            result += abs(reduce(lambda acc, m: acc + individual[m * D + d], range(M), 0) - 2)  # 値そのものをしようしているので、absとかも使えます

        return result

    # 同じ人と別の日に出社しないという制約を追加します
    def different_member():
        result = 0

        for m1 in range(M):
            for m2 in range(m1 + 1, M):
                for d1 in range(D):
                    for d2 in range(d1 + 1, D):
                        result += individual[m1 * D + d1] * individual[m2 * D + d1] * individual[m1 * D + d2] * individual[m2 * D + d2]

        return result

    # 複数の評価の視点を、それぞれの視点での評価結果を要素とするタプルで返します
    return (member_size(), different_member())

# どのように遺伝的アルゴリズムするのかをDEAPで定義します
creator.create('Fitness', base.Fitness, weights=(-1.0, -0.5))
creator.create('Individual', list, fitness=creator.Fitness)

toolbox = base.Toolbox()

toolbox.register('attribute', randint, 0, 1)
toolbox.register('individual', tools.initRepeat, creator.Individual, toolbox.attribute, n=M * D)
toolbox.register('population', tools.initRepeat, list, toolbox.individual)
toolbox.register('mate', tools.cxTwoPoint)
toolbox.register('mutate', tools.mutFlipBit, indpb=0.05)
toolbox.register('select', tools.selTournament, tournsize=3)
toolbox.register('evaluate', evaluate)

# 再現性のために、ランダムのシードを固定します
seed(1)

# 遺伝アルゴリズムで問題を解きます
population, _ = algorithms.eaSimple(toolbox.population(n=100), toolbox, 0.5, 0.2, 300, verbose=False)

# 最も良い解を取得します
individual = tools.selBest(population, 1)[0]

# 結果を出力します
print(f'fitness:\t{individual.fitness.values}')

# 非単位で、出社する社員を出力します
for d in range(D):
    print(tuple(keep(lambda m: 'ABCDE'[m] if individual[m * D + d] else False, range(M))))
