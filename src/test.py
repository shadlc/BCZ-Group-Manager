# 测试机
# 重复实验10000次，每次生成100个0或1，其中0占比50%，统计其中连续0的最长长度。


import random
import sys

# j = 0
# # j从0.1到0.9，表示1的比例
# while j < 1:
#     j += 0.01
#     ans = 0
#     count = 0

#     while count < 1000:
#         sequence = [1 if random.random() < j else 0 for _ in range(10000)]
#         length = 0
#         max_length = 0
#         for i in range(len(sequence)):
#             if sequence[i] == 0:
#                 length += 1
#             else:
#                 if length > max_length:
#                     max_length = length
#                 length = 0
#         if length > max_length:
#             max_length = length
#         ans += max_length
#         count += 1

#     sys.stdout.write(f'{ans/1000} ')
#     # print("The expectancy of the longest consecutive 0s length is:", ans/10000)


#  数学计算

one = 1
while one > 0:
    one -= 0.01
    zero = 1 - one
    e = 100
    length = 0
    while length < 100:
        length += 1
        e *= one # 
        if e <= length/10:
            sys.stdout.write(f'{length} ')
            break



    