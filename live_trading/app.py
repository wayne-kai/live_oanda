from flask import Flask, request, Response
import threading, time
from trade import Status, trade_attempt

class LiveTrading:
    def __init__(self):
        self.thread = None
        self.status = Status.Inactive
        self.status_lock = threading.Lock()
        self.params = {}
        self.params_lock = threading.Lock()

    def start(self):
        if not self.thread:
            self.thread = threading.Thread(target=self.run)
            self.thread.daemon = True
            self.thread.start()

    def run(self):
        # Your infinite addition logic here
        a = 0
        while True:
            print("current status: ", self.get_status())
            if self.get_status() == Status.Active:
                params = self.get_params()

                trade_attempt(
                    # check if key params exist first
                    model=params['model'],
                    take_profit=params['take_profit'],
                    stop_loss=params['stop_loss'],
                    status=self.status)
                
            
            time.sleep(2)

    def get_status(self):
        with self.status_lock:
            return self.status

    def set_status(self, new_status: Status):
        with self.status_lock:
            self.status = new_status

    def get_params(self):
        with self.params_lock:
            return self.params

    def set_params(self, params):
        with self.params_lock:
            print("set params: ", params)
            self.params = params

# app function for waitress
def create_app():
    app = Flask(__name__)

    ltrading = LiveTrading()
    ltrading.start()

    @app.route('/activate', methods=['POST'])
    def activate():
        # custom tp/sl
        tp = request.json.get('take_profit')
        sl = request.json.get('stop_loss')
        model = request.json.get('model')

        if ltrading.get_status() == Status.Active:
            return Response("{'error':'Cannot activate when still active'}", status=201, mimetype='application/json')

        ltrading.set_params({'take_profit': tp, 'stop_loss': sl, 'model': model})
        ltrading.set_status(Status.Active)

        print("activated")
        return "Live trading activated\n"

    @app.route('/deactivate', methods=['POST'])
    def deactivate():
        ltrading.set_status(Status.Inactive)
        print("deactivated")
        return "Live trading deactivated\n"
    
    @app.route('/stop', methods=['POST'])
    def stop():
        ltrading.set_status(Status.Stop)
        print("stopped")
        return "Live trading stopped\n"

    return app