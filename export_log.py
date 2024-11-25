import sqlite3
import datetime
import xlsxwriter
import os

conn = sqlite3.connect('data.db')
# 从GROUPS表读取GROUP_ID对应组名
cursor = conn.execute("SELECT GROUP_ID, NAME FROM GROUPS")
group_dict = {}
for row in cursor:
    group_dict[str(row[0])] = row[1]
print(group_dict)

# 从FILTER_LOG表中导出今天的数据到表格
date_str = datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')
date_str_end = datetime.datetime.now().strftime('%Y-%m-%d 23:59:59')
cursor = conn.execute("SELECT * FROM FILTER_LOG WHERE DATETIME BETWEEN ? AND ? ORDER BY GROUP_ID, DATETIME" , (date_str, date_str_end))
# "GROUP_ID","DATETIME","STRATEGY_NAME","MEMBER_COUNT","NEWBIES_COUNT","ACCEPTED_COUNT","ACCEPT_LIST","REMOVE_LIST","QUIT_LIST"
file_name = datetime.datetime.now().strftime('%Y年第%W周%w') + '.xlsx'
file_path = './filter_log/'
if not os.path.exists(file_path):
    os.makedirs(file_path)

header = ['组ID', '组名', '日期', '策略名称', '成员数量', '新人数量', '接受数量', '接受列表', '移除列表', '退出列表']
# 创建excel文件
workbook = xlsxwriter.Workbook(file_path + file_name)
# 设置默认字体：等线
font_format = workbook.add_format({'font_name': 'Arial'})
# 对每个组创建一个sheet
current_group_id = None
worksheet = None
row_num = 0
for row in cursor:
    group_id = row[0]
    if group_id!= current_group_id:
        current_group_id = group_id
        group_name = group_dict[group_id]
        worksheet = workbook.add_worksheet(group_name)
        # 写入表头
        for i in range(len(header)):
            worksheet.write(0, i, header[i])
        row_num = 1
        # 调整宽度
        worksheet.set_column(2, 2, 25)
        worksheet.set_column(3, 3, 95)
    # 写入数据
    group_id = row[0]
    group_name = group_dict[group_id]
    datetime_str = row[1]
    strategy_name = row[2]
    member_count = row[3]
    newbies_count = row[4]
    accepted_count = row[5]
    accept_list = row[6]
    remove_list = row[7]
    quit_list = row[8]
    worksheet.write(row_num, 0, group_id, font_format)
    worksheet.write(row_num, 1, group_name, font_format)
    worksheet.write(row_num, 2, datetime_str, font_format)
    worksheet.write(row_num, 3, strategy_name, font_format)
    worksheet.write(row_num, 4, member_count, font_format)
    worksheet.write(row_num, 5, newbies_count, font_format)
    worksheet.write(row_num, 6, accepted_count, font_format)
    worksheet.write(row_num, 7, accept_list, font_format)
    worksheet.write(row_num, 8, remove_list, font_format)
    worksheet.write(row_num, 9, quit_list, font_format)
    row_num += 1

workbook.close()
