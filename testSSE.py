from flask import Flask, Response, stream_with_context, render_template
import threading
import time

app = Flask(__name__)

# 处理SSE连接
clients_message_lock = threading.Lock()
clients_message = []
def generator():
    i = 0
    while True:
        i += 1
        with clients_message_lock:
            for queue in clients_message:
                queue.append(f'Server message {i}')
        time.sleep(1)

thread = threading.Thread(target=generator)
@app.route('/')
def index():
    if not thread.is_alive():
        thread.start()
    return render_template('testSSE.html')
@app.route('/events')
def events():
    def generate():
        client_id = len(clients_message)
        clients_message.append([])
        try:
            i = 0
            while True:
                while len(clients_message[client_id]) > i:
                    message = clients_message[client_id][i]
                    i += 1
                    yield f'data: {i}.{message}\n\n'
                time.sleep(1)
        except GeneratorExit:
            with clients_message_lock:
                clients_message.pop(client_id)

    return Response(stream_with_context(generate()), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
