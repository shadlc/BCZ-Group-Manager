'''【独立工具】提取FILTER_LOG中的数据进行绘图，用以观察小班组的策略执行效果。包括筛选开始结束时间、最高最低和最终排名'''
import datetime
import sqlite3
import os
# 设置路径为当前文件夹
os.chdir(os.path.dirname(__file__))
conn = sqlite3.connect('data.db')
cursor = conn.cursor()
cursor.execute('''SELECT GROUP_ID, DATETIME, STRATEGY_NAME FROM FILTER_LOG ORDER BY DATETIME ASC''')
result = cursor.fetchall()
group_dict = {}
for row in result:
    # 按GROUP_ID分组
    if row[0] is None:
        continue
    if row[0] not in group_dict:
        group_dict[row[0]] = []
    group_dict[row[0]].append((row[1], row[2]))

result = {}
now = datetime.datetime.now()
for group_id, log_list in group_dict.items():
    print(f"Group {group_id}:")
    # 找到每个GROUP_ID每个DATETIME的最早时间和最晚时间
    earliest_time = now
    latest_time = now
    lowest_rank = 0
    highest_rank = 0
    final_rank = 0
    date = ""
    new_date = ""
    result[group_id] = {}
    for log_list_item in log_list:
        if log_list_item[0] is None:
            continue
        time = datetime.datetime.strptime(log_list_item[0], "%Y-%m-%d %H:%M:%S %U周%w") # HH:MM:SS
        new_date = log_list_item[0].split()[0]
        if new_date == "":
            continue
        if new_date != date and date != "":
            result[group_id][date] = (earliest_time, latest_time, lowest_rank, highest_rank, final_rank)
            earliest_time = now
            latest_time = now
            lowest_rank = 0
            highest_rank = 0
            final_rank = 0
        date = new_date
        rank = int(log_list_item[1].split(']')[0].split('段')[1])
        if time < earliest_time or earliest_time == now:
            earliest_time = time
        if time > latest_time or latest_time == now:
            latest_time = time
            final_rank = rank
        if rank > lowest_rank:
            lowest_rank = rank
        if rank < highest_rank or highest_rank == 0:
            highest_rank = rank
    if date != "":
        result[group_id][date] = (earliest_time, latest_time, lowest_rank, highest_rank, final_rank)
    # print(result[group_id])

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 创建两个子图，上下排列
fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(12, 8))

# 设置颜色循环
colors = plt.cm.tab10.colors

# 绘制第一个子图（Rank）
for idx, group_id in enumerate(result.keys()):
    group_data = result[group_id]
    dates = sorted(group_data.keys(), key=lambda x: datetime.datetime.strptime(x, "%Y-%m-%d"))
    date_objs = [datetime.datetime.strptime(d, "%Y-%m-%d") for d in dates]
    
    # 提取rank相关数据
    final_ranks = [group_data[d][4] for d in dates]
    highest_ranks = [group_data[d][3] for d in dates]
    lowest_ranks = [group_data[d][2] for d in dates]
    
    # 计算误差条
    y_err_lower = [fr - hr for fr, hr in zip(final_ranks, highest_ranks)]
    y_err_upper = [lr - fr for fr, lr in zip(final_ranks, lowest_ranks)]
    
    # 绘制折线图和误差条
    ax1.errorbar(
        date_objs, final_ranks,
        yerr=[y_err_lower, y_err_upper],
        label=f'Group {group_id}',
        color=colors[idx % len(colors)],
        marker='o',
        linestyle='-'
    )

ax1.set_ylabel('Rank')
ax1.legend(loc='upper left')
ax1.set_title('Rank')
ax1.grid(True)

# 绘制第二个子图（Time）
for idx, group_id in enumerate(result.keys()):
    group_data = result[group_id]
    dates = sorted(group_data.keys(), key=lambda x: datetime.datetime.strptime(x, "%Y-%m-%d"))
    date_objs = [datetime.datetime.strptime(d, "%Y-%m-%d") for d in dates]
    
    # 提取时间数据并转换格式
    earliest_times = [group_data[d][0] for d in dates]
    latest_times = [group_data[d][1] for d in dates]

    # 将所有datetime格式的date设置为今天
    today = datetime.datetime.now().date()
    for i in range(len(earliest_times)):
        earliest_times[i] = datetime.datetime.combine(today, earliest_times[i].time())
        latest_times[i] = datetime.datetime.combine(today, latest_times[i].time())
    
    # 转换为matplotlib数值格式
    latest_nums = [mdates.date2num(t) for t in latest_times]
    earliest_nums = [mdates.date2num(t) for t in earliest_times]
    middle_nums = [(ln + en) / 2 for ln, en in zip(latest_nums, earliest_nums)]
    
    # 计算时间误差条（从最早到最晚）
    y_err_lower = [ln - en for ln, en in zip(latest_nums, earliest_nums)]
    
    # 绘制折线图和误差条
    ax2.errorbar(
        date_objs, latest_nums,
        yerr=[y_err_lower, [0]*len(y_err_lower)],
        label=f'Group {group_id}',
        color=colors[idx % len(colors)],
        marker='o',
        linestyle='-'
    )

# 设置时间格式
ax2.yaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax2.set_ylabel('Time (HH:MM)')
ax2.grid(True)
ax2.set_title('Latest Time')

# 设置公共x轴格式
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.xticks(rotation=45)
plt.xlabel('Date')

# 自动调整布局并显示
fig.tight_layout()
plt.show()