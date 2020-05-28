from functools import reduce
from funcy     import *
from pulp      import *

M = 5   # 社員の数
D = 10  # 日数

# 問題の中で使用する変数を定義します
xs = LpVariable.dicts('x', (range(M), range(D)), 0, 1, 'Binary')

# 問題を定義します。ここから……
problem = LpProblem('shift-scheduling-problem', LpMinimize)

for d in range(D):
    problem += reduce(lambda acc, m: acc + xs[m][d], range(M), 0) >= 2

for m1 in range(M):
    for m2 in range(m1 + 1, M):
        for d1 in range(D):
            for d2 in range(d1 + 1, D):
                problem += xs[m1][d1] + xs[m2][d1] + xs[m1][d2] + xs[m2][d2] <= 3  # 不等号（<）は使用できなかったので、<= 3で

# problem.writeLP('shift-scheduling-problem')
# ……ここまで。問題を定義します

status = problem.solve()

print(LpStatus[status])

for d in range(D):
    print(tuple(keep(lambda m: 'ABCDE'[m] if xs[m][d].value() else False, range(M))))
