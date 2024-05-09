import base64

result = base64.b64decode('VGhpcyBpcyBhIHRlc3Q=')

# 将转换为二进制数据
binary_data = result.decode('utf-8')

# 打印二进制数据    
print(binary_data)
