from itertools import combinations, cycle

# 重複しない社員2名の組合せを生成します
members = cycle(combinations('ABCDE', 2))  # 10日ならcycleしなくても良いのですけど、念の為

# 10日分、出力します
for _ in range(10):
    print(next(members))
