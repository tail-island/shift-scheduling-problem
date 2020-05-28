from functools import reduce
from funcy     import *
from pulp      import *

M = 5   # 社員の数
D = 10  # 日数

# 問題の中で使用する変数を定義します
xs = LpVariable.dicts('x', (range(M), range(D)), 0, 1, 'Binary')

# 問題を定義します。ここから……
problem = LpProblem('shift-scheduling-problem', LpMinimize)

# 1日に2名以上、かつ、できるだけ少なくという制約を追加します。2名より多くても少なくてもペナルティが発生するようになっています
for d in range(D):
    problem += reduce(lambda acc, m: acc + xs[m][d], range(M), 0) >= 2

# 同じ人と別の日に出社しないという制約を追加します
for m1 in range(M):
    for m2 in range(m1 + 1, M):
        for d1 in range(D):
            for d2 in range(d1 + 1, D):
                problem += xs[m1][d1] + xs[m2][d1] + xs[m1][d2] + xs[m2][d2] <= 3  # 不等号（<）は使用できなかったので、<= 3で

# problem.writeLP('shift-scheduling-problem')
# ……ここまで。問題を定義します

# 整数計画法で、問題を解きます
status = problem.solve()

# 結果を出力します
print(LpStatus[status])

# 日単位で、出社する社員を出力します
for d in range(D):
    print(tuple(keep(lambda m: 'ABCDE'[m] if xs[m][d].value() else False, range(M))))
